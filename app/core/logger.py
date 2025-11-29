"""
Structured Logging System for Python Project
==============================================

This module provides a comprehensive structured logging system using structlog with:
- Colored console output
- Separate log levels for console and files
- Multiple log types: Error, App, Debug, Security
- Daily log rotation
- Graylog-compatible JSON output

Author: Auto-generated
Date: 2025
"""

import logging
import logging.handlers
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import OrderedDict
import json
import shutil

import structlog
from structlog.processors import JSONRenderer
from colorlog import ColoredFormatter
import pytz

from app.core.config import settings


# Global state
_initialized = False
_initialization_lock = threading.Lock()
_log_rotator: Optional['DailyLogRotator'] = None
_used_log_types: set = set()


class DailyLogRotator:
    """
    Handles automatic daily log file rotation with proper file management.
    Maintains a single current log file and archives old logs with .hist.log suffix.
    """

    def __init__(self, log_dir: str = "logs", check_timeout_seconds: int = 300):
        """
        Initialize the daily log rotator.

        Args:
            log_dir: Directory to store log files
            check_timeout_seconds: Timeout between date checks (default: 5 minutes)
        """
        self.log_dir = Path(log_dir)
        self.check_timeout_seconds = check_timeout_seconds
        self.last_check_time = datetime.now(pytz.UTC)
        self.current_date = datetime.now(pytz.UTC).strftime("%Y-%m-%d")
        self.handlers: Dict[str, Any] = {}
        self.lock = threading.Lock()

        # Start background thread for periodic checking
        self._start_background_checker()

    def _start_background_checker(self):
        """Start background thread for periodic date checking."""
        def check_loop():
            while True:
                try:
                    time.sleep(self.check_timeout_seconds)
                    self._check_and_rotate_if_needed()
                except Exception as e:
                    # Log error but continue running
                    print(f"Error in background date checker: {e}")

        checker_thread = threading.Thread(target=check_loop, daemon=True)
        checker_thread.start()

    def _check_and_rotate_if_needed(self) -> bool:
        """
        Check if date has changed and rotate log files if necessary.

        Returns:
            True if rotation occurred, False otherwise
        """
        with self.lock:
            current_time = datetime.now(pytz.UTC)

            # Check if enough time has passed since last check
            if (current_time - self.last_check_time).total_seconds() < self.check_timeout_seconds:
                return False

            # Check if date has changed
            new_date = current_time.strftime("%Y-%m-%d")
            if new_date == self.current_date:
                self.last_check_time = current_time
                return False

            # Date has changed, rotate log files
            self._rotate_log_files(new_date)
            self.current_date = new_date
            self.last_check_time = current_time
            return True

    def _rotate_log_files(self, new_date: str):
        """Rotate log files to new date with proper archiving."""
        try:
            # Archive current log files
            self._archive_current_logs()
            print(f"Log files rotated to new date: {new_date}")
        except Exception as e:
            print(f"Error rotating log files: {e}")

    def _archive_current_logs(self):
        """Archive current log files with .hist.log suffix."""
        try:
            # Define log types and their subdirectories
            log_types = {
                'error': 'error',
                'app': 'app',
                'debug': 'debug',
                'security': 'security'
            }

            for log_type, subdir in log_types.items():
                log_dir = self.log_dir / subdir
                if not log_dir.exists():
                    continue

                # Archive all .log files in this directory
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_size > 0:
                        # Create archive filename with .hist.log suffix
                        archive_name = f"{log_file.stem}-{self.current_date}.hist.log"
                        archive_path = log_file.parent / archive_name

                        # Copy current log to archive (don't move, as file handlers are still open)
                        try:
                            shutil.copy2(str(log_file), str(archive_path))
                            # Truncate the original file
                            with open(log_file, 'w'):
                                pass
                            print(f"Archived {log_type}/{log_file.name} to {archive_name}")
                        except Exception as e:
                            print(f"Error archiving {log_file}: {e}")

        except Exception as e:
            print(f"Error archiving log files: {e}")

    def check_and_rotate_if_needed(self) -> bool:
        """
        Public method to check and rotate logs if needed.

        Returns:
            True if rotation occurred, False otherwise
        """
        return self._check_and_rotate_if_needed()


def _get_log_level(level_str: str) -> int:
    """
    Convert log level string to logging level constant.

    Args:
        level_str: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logging level constant
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return level_map.get(level_str.upper(), logging.INFO)


def _create_log_directories():
    """Create log directories for each log type."""
    log_dir = Path(settings.LOG_DIR)
    
    # Always create error, app, and debug directories
    for subdir in ['error', 'app', 'debug']:
        dir_path = log_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Security directory is created only when first used


def _track_log_type(log_type: str):
    """Track which log types have been used."""
    global _used_log_types
    _used_log_types.add(log_type)
    
    # Create security directory if needed
    if log_type == 'security':
        security_dir = Path(settings.LOG_DIR) / 'security'
        security_dir.mkdir(parents=True, exist_ok=True)


def _add_log_level(logger, method_name: str, event_dict: dict) -> dict:
    """
    Processor to add log level to event dict.
    """
    if method_name:
        event_dict['level'] = method_name.upper()
    return event_dict


def _add_timestamp(logger, method_name: str, event_dict: dict) -> dict:
    """
    Processor to add timezone-aware timestamp to event dict.
    Uses UTC timezone with proper ISO format including timezone offset (+00:00).
    """
    utc_now = datetime.now(pytz.UTC)
    event_dict['timestamp'] = utc_now.isoformat()
    return event_dict


def _add_timezone_aware_timestamp(logger, method_name: str, event_dict: dict) -> dict:
    """
    Processor to add timezone-aware timestamp for foreign loggers (stdlib).
    Replaces structlog's TimeStamper to use pytz and preserve timezone offset.
    """
    if 'timestamp' not in event_dict:
        utc_now = datetime.now(pytz.UTC)
        event_dict['timestamp'] = utc_now.isoformat()
    return event_dict


def _order_json_fields(logger, method_name: str, event_dict: dict) -> dict:
    """
    Processor to reorder fields in JSON output: timestamp, level, logger first.
    """
    ordered = OrderedDict()
    
    # Check for different possible field names used by structlog
    # TimeStamper adds 'timestamp', add_log_level adds 'level', add_logger_name adds 'logger'
    timestamp_key = None
    for key in ['timestamp', 'time', '@timestamp']:
        if key in event_dict:
            timestamp_key = key
            break
    
    level_key = None
    for key in ['level', 'log_level', 'severity']:
        if key in event_dict:
            level_key = key
            break
    
    logger_key = None
    for key in ['logger', 'name', 'logger_name']:
        if key in event_dict:
            logger_key = key
            break
    
    # Always put these fields first in this order
    if timestamp_key:
        ordered[timestamp_key] = event_dict.pop(timestamp_key)
    if level_key:
        ordered[level_key] = event_dict.pop(level_key)
    if logger_key:
        ordered[logger_key] = event_dict.pop(logger_key)
    
    # Add remaining fields
    for key, value in event_dict.items():
        ordered[key] = value
    
    return ordered


class OrderedJSONRenderer:
    """
    Custom JSON renderer that ensures timestamp, level, logger are first.
    """
    
    def __call__(self, logger, method_name: str, event_dict: dict) -> str:
        """
        Render event_dict to JSON with specific field ordering.
        
        Args:
            logger: Logger instance
            method_name: Method name
            event_dict: Event dictionary
        
        Returns:
            JSON string with timestamp, level, logger first
        """
        ordered = OrderedDict()
        
        # Check for different possible field names and add them first
        for key in ['timestamp', 'time', '@timestamp']:
            if key in event_dict:
                ordered[key] = event_dict[key]
                break
        
        for key in ['level', 'log_level', 'severity']:
            if key in event_dict:
                ordered[key] = event_dict[key]
                break
        
        for key in ['logger', 'name', 'logger_name']:
            if key in event_dict:
                ordered[key] = event_dict[key]
                break
        
        # Add all other fields
        for key, value in event_dict.items():
            if key not in ordered:
                ordered[key] = value
        
        # Serialize to JSON, preserving order
        # Python's json module preserves dict order in Python 3.7+
        return json.dumps(ordered, default=str, ensure_ascii=False)


def setup_logging():
    """
    Setup the structured logging system with console and file handlers.
    This function should be called once at application startup.
    """
    global _initialized, _log_rotator
    
    with _initialization_lock:
        if _initialized:
            return
        
        # Create log directories
        _create_log_directories()
        
        # Initialize log rotator
        _log_rotator = DailyLogRotator(
            log_dir=settings.LOG_DIR,
            check_timeout_seconds=settings.LOG_ROTATION_TIMEOUT
        )
        
        # Get log levels
        console_level = _get_log_level(settings.CONSOLE_LOG_LEVEL)
        file_level = _get_log_level(settings.FILE_LOG_LEVEL)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                _add_timestamp,  # Use timezone-aware timestamp
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Setup console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        
        console_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s%(reset)s | "
            "%(log_color)s%(levelname)-8s%(reset)s | "
            "%(cyan)s%(name)s%(reset)s | "
            "%(message)s",
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Accept all levels, filter at handler level
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        
        # Setup file handlers for each log type
        _setup_file_handlers(file_level)
        
        _initialized = True
        
        # Log initialization message
        logger = get_logger(__name__)
        logger.info(
            "Logging system initialized",
            console_level=settings.CONSOLE_LOG_LEVEL,
            file_level=settings.FILE_LOG_LEVEL,
            log_dir=settings.LOG_DIR
        )


def _setup_file_handlers(file_level: int):
    """
    Setup file handlers for each log type.
    
    Args:
        file_level: File logging level
    """
    log_dir = Path(settings.LOG_DIR)
    
    # JSON formatter for file logs (Graylog-compatible)
    # Custom processor chain to ensure field order: timestamp, level, logger, then rest
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=OrderedJSONRenderer(),
        foreign_pre_chain=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            _add_timezone_aware_timestamp,  # Add timezone-aware timestamp
            _order_json_fields,  # Reorder fields
        ],
    )
    
    # Setup app log handler
    app_handler = logging.FileHandler(
        log_dir / 'app' / 'app.log',
        mode='a',
        encoding='utf-8'
    )
    app_handler.setLevel(file_level)
    app_handler.setFormatter(json_formatter)
    app_handler.addFilter(lambda record: record.levelno < logging.ERROR)  # Exclude errors
    
    # Setup error log handler (always ERROR and above)
    error_handler = logging.FileHandler(
        log_dir / 'error' / 'error.log',
        mode='a',
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # Setup default debug log handler
    debug_handler = logging.FileHandler(
        log_dir / 'debug' / 'debug.log',
        mode='a',
        encoding='utf-8'
    )
    debug_handler.setLevel(file_level)
    debug_handler.setFormatter(json_formatter)
    
    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(debug_handler)


class StructuredLogger:
    """
    Wrapper around structlog logger providing additional functionality.
    """
    
    def __init__(self, name: str, log_type: str = 'app', sublog: Optional[str] = None):
        """
        Initialize a structured logger.
        
        Args:
            name: Logger name (usually __name__)
            log_type: Type of log (app, error, debug, security)
            sublog: Optional sublog name for debug logs
        """
        self.name = name
        self.log_type = log_type
        self.sublog = sublog
        self._logger = structlog.get_logger(name)
        
        # Track log type usage
        _track_log_type(log_type)
        
        # Setup sublog handler if specified
        if sublog and log_type == 'debug':
            self._setup_sublog_handler(sublog)
    
    def _setup_sublog_handler(self, sublog: str):
        """
        Setup a specific sublog handler for debug logs.
        
        Args:
            sublog: Sublog name
        """
        log_dir = Path(settings.LOG_DIR) / 'debug'
        sublog_file = log_dir / f"{sublog}.log"
        
        # JSON formatter for file logs with field ordering
        json_formatter = structlog.stdlib.ProcessorFormatter(
            processor=OrderedJSONRenderer(),
            foreign_pre_chain=[
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                _add_timezone_aware_timestamp,  # Add timezone-aware timestamp
                _order_json_fields,  # Reorder fields
            ],
        )
        
        # Create handler for this sublog
        sublog_handler = logging.FileHandler(
            sublog_file,
            mode='a',
            encoding='utf-8'
        )
        sublog_handler.setLevel(_get_log_level(settings.FILE_LOG_LEVEL))
        sublog_handler.setFormatter(json_formatter)
        
        # Add to the underlying stdlib logger
        stdlib_logger = logging.getLogger(self.name)
        stdlib_logger.addHandler(sublog_handler)
    
    def _ensure_rotation(self):
        """Ensure log rotation is checked before logging."""
        global _log_rotator
        if _log_rotator:
            _log_rotator.check_and_rotate_if_needed()
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._ensure_rotation()
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._ensure_rotation()
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self._ensure_rotation()
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        self._ensure_rotation()
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self._ensure_rotation()
        self._logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log an exception with traceback."""
        self._ensure_rotation()
        self._logger.exception(message, **kwargs)


def get_logger(name: str = None, sublog: Optional[str] = None) -> StructuredLogger:
    """
    Get a logger instance for general application logging.
    
    Args:
        name: Logger name (usually __name__)
        sublog: Optional sublog name for debug logs
    
    Returns:
        StructuredLogger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id=123, ip="192.168.1.1")
    """
    if not _initialized:
        setup_logging()
    
    if name is None:
        name = 'app'
    
    return StructuredLogger(name, log_type='app', sublog=sublog)


def get_error_logger(name: str = None) -> StructuredLogger:
    """
    Get a logger instance for error logging.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        StructuredLogger instance configured for error logging
    
    Example:
        error_logger = get_error_logger(__name__)
        error_logger.error("Database connection failed", db_host="localhost")
    """
    if not _initialized:
        setup_logging()
    
    if name is None:
        name = 'error'
    
    return StructuredLogger(name, log_type='error')


def get_app_logger(name: str = None) -> StructuredLogger:
    """
    Get a logger instance for application logging.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        StructuredLogger instance configured for app logging
    
    Example:
        app_logger = get_app_logger(__name__)
        app_logger.info("Application started", version="1.0.0")
    """
    if not _initialized:
        setup_logging()
    
    if name is None:
        name = 'app'
    
    return StructuredLogger(name, log_type='app')


def get_debug_logger(name: str = None, sublog: Optional[str] = None) -> StructuredLogger:
    """
    Get a logger instance for debug logging.
    
    Args:
        name: Logger name (usually __name__)
        sublog: Optional sublog name (e.g., 'api', 'database', 'middleware')
    
    Returns:
        StructuredLogger instance configured for debug logging
    
    Example:
        # Default debug.log
        debug_logger = get_debug_logger(__name__)
        debug_logger.debug("Processing request", request_id="abc123")
        
        # Custom sublog: logs/debug/api.log
        api_debug_logger = get_debug_logger(__name__, sublog="api")
        api_debug_logger.debug("API call", endpoint="/users", method="GET")
    """
    if not _initialized:
        setup_logging()
    
    if name is None:
        name = 'debug'
    
    return StructuredLogger(name, log_type='debug', sublog=sublog)


def get_security_logger(name: str = None) -> StructuredLogger:
    """
    Get a logger instance for security event logging.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        StructuredLogger instance configured for security logging
    
    Example:
        security_logger = get_security_logger(__name__)
        security_logger.info(
            "Login attempt",
            user="john.doe",
            ip="192.168.1.1",
            success=True
        )
    """
    if not _initialized:
        setup_logging()
    
    if name is None:
        name = 'security'
    
    # Track security log type and create directory
    _track_log_type('security')
    
    # Setup security log handler if not already done
    log_dir = Path(settings.LOG_DIR) / 'security'
    security_file = log_dir / 'security.log'
    
    if not security_file.exists():
        # JSON formatter for file logs with field ordering
        json_formatter = structlog.stdlib.ProcessorFormatter(
            processor=OrderedJSONRenderer(),
            foreign_pre_chain=[
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                _add_timezone_aware_timestamp,  # Add timezone-aware timestamp
                _order_json_fields,  # Reorder fields
            ],
        )
        
        # Create security handler
        security_handler = logging.FileHandler(
            security_file,
            mode='a',
            encoding='utf-8'
        )
        security_handler.setLevel(_get_log_level(settings.FILE_LOG_LEVEL))
        security_handler.setFormatter(json_formatter)
        
        # Add filter to only capture security logs
        security_handler.addFilter(lambda record: 'security' in record.name.lower())
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(security_handler)
    
    return StructuredLogger(name, log_type='security')


def get_used_log_types() -> List[str]:
    """
    Get list of log types that have been used in the application.
    
    Returns:
        List of log type names
    """
    return list(_used_log_types)


def force_log_rotation() -> bool:
    """
    Force immediate log rotation check and rotation if needed.
    
    Returns:
        True if rotation occurred, False otherwise
    """
    global _log_rotator
    if _log_rotator:
        return _log_rotator.check_and_rotate_if_needed()
    return False

