"""
Logging Helper Utilities
=========================

This module provides helper functions and context managers for common logging patterns.
"""

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional
import uuid

from app.core.logger import get_logger


@contextmanager
def log_context(**context_vars):
    """
    Context manager to add context variables to all logs within the context.
    
    Args:
        **context_vars: Key-value pairs to add to log context
    
    Example:
        with log_context(request_id="abc123", user_id=456):
            logger.info("Processing request")  # Will include request_id and user_id
    """
    logger = get_logger()
    # Store the context in thread-local storage if needed
    # For now, we'll just pass through
    try:
        yield context_vars
    finally:
        pass


def log_execution_time(logger=None, log_level: str = "info"):
    """
    Decorator to log execution time of a function.
    
    Args:
        logger: Logger instance (if None, creates a new one)
        log_level: Log level to use (debug, info, warning, error)
    
    Example:
        @log_execution_time()
        def process_data():
            # ... processing ...
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                log_method = getattr(logger, log_level.lower(), logger.info)
                log_method(
                    f"Function executed successfully",
                    function=func.__name__,
                    execution_time_seconds=round(execution_time, 4),
                    module=func.__module__
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function execution failed",
                    function=func.__name__,
                    execution_time_seconds=round(execution_time, 4),
                    module=func.__module__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator


def log_function_call(logger=None, log_args: bool = False, log_result: bool = False):
    """
    Decorator to log function calls with optional argument and result logging.
    
    Args:
        logger: Logger instance (if None, creates a new one)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
    
    Example:
        @log_function_call(log_args=True)
        def calculate_total(price, quantity):
            return price * quantity
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            log_data = {
                "function": func.__name__,
                "module": func.__module__
            }
            
            if log_args:
                log_data["args"] = str(args) if args else None
                log_data["kwargs"] = kwargs if kwargs else None
            
            logger.debug("Function called", **log_data)
            
            try:
                result = func(*args, **kwargs)
                
                if log_result:
                    log_data["result"] = str(result)
                
                logger.debug("Function completed", **log_data)
                return result
            except Exception as e:
                log_data["error"] = str(e)
                log_data["error_type"] = type(e).__name__
                logger.error("Function failed", **log_data)
                raise
        
        return wrapper
    return decorator


class RequestLogger:
    """
    Helper class for logging HTTP requests with consistent format.
    """
    
    def __init__(self, logger=None):
        """
        Initialize request logger.
        
        Args:
            logger: Logger instance (if None, creates a new one)
        """
        self.logger = logger or get_logger("request")
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        **extra_data
    ):
        """
        Log an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            **extra_data: Additional data to log
        """
        log_data = {
            "http_method": method,
            "http_path": path,
            "http_status_code": status_code,
            "duration_ms": duration_ms,
            **extra_data
        }
        
        if status_code:
            if status_code >= 500:
                self.logger.error("HTTP request completed", **log_data)
            elif status_code >= 400:
                self.logger.warning("HTTP request completed", **log_data)
            else:
                self.logger.info("HTTP request completed", **log_data)
        else:
            self.logger.info("HTTP request started", **log_data)


class SecurityLogger:
    """
    Helper class for logging security events with consistent format.
    """
    
    def __init__(self, logger=None):
        """
        Initialize security logger.
        
        Args:
            logger: Logger instance (if None, creates a security logger)
        """
        from app.core.logger import get_security_logger
        self.logger = logger or get_security_logger("security")
    
    def log_authentication_attempt(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
        **extra_data
    ):
        """
        Log an authentication attempt.
        
        Args:
            username: Username attempting to authenticate
            success: Whether authentication was successful
            ip_address: IP address of the requester
            reason: Reason for failure (if applicable)
            **extra_data: Additional data to log
        """
        log_data = {
            "event_type": "authentication",
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "reason": reason,
            **extra_data
        }
        
        if success:
            self.logger.info("Authentication successful", **log_data)
        else:
            self.logger.warning("Authentication failed", **log_data)
    
    def log_authorization_check(
        self,
        user: str,
        resource: str,
        action: str,
        allowed: bool,
        **extra_data
    ):
        """
        Log an authorization check.
        
        Args:
            user: User requesting access
            resource: Resource being accessed
            action: Action being performed
            allowed: Whether access was granted
            **extra_data: Additional data to log
        """
        log_data = {
            "event_type": "authorization",
            "user": user,
            "resource": resource,
            "action": action,
            "allowed": allowed,
            **extra_data
        }
        
        if allowed:
            self.logger.info("Access granted", **log_data)
        else:
            self.logger.warning("Access denied", **log_data)
    
    def log_security_event(
        self,
        event_type: str,
        severity: str = "info",
        **extra_data
    ):
        """
        Log a generic security event.
        
        Args:
            event_type: Type of security event
            severity: Severity level (info, warning, error, critical)
            **extra_data: Additional data to log
        """
        log_data = {
            "event_type": event_type,
            **extra_data
        }
        
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method("Security event", **log_data)


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracking.
    
    Returns:
        Unique request ID string
    """
    return str(uuid.uuid4())


def create_log_event(
    event_type: str,
    message: str,
    **attributes
) -> Dict[str, Any]:
    """
    Create a structured log event dictionary.
    
    Args:
        event_type: Type of event (e.g., "user_action", "system_event")
        message: Human-readable message
        **attributes: Additional event attributes
    
    Returns:
        Dictionary with structured event data
    
    Example:
        event = create_log_event(
            "user_action",
            "User updated profile",
            user_id=123,
            fields_updated=["email", "phone"]
        )
        logger.info(event["message"], **event["attributes"])
    """
    return {
        "event_type": event_type,
        "message": message,
        "attributes": attributes
    }


@contextmanager
def log_operation(
    operation_name: str,
    logger=None,
    **context_data
):
    """
    Context manager to log the start and end of an operation.
    
    Args:
        operation_name: Name of the operation
        logger: Logger instance (if None, creates a new one)
        **context_data: Additional context data to include in logs
    
    Example:
        with log_operation("database_migration", version="1.2.0"):
            # Perform migration
            migrate_database()
    """
    if logger is None:
        logger = get_logger()
    
    operation_id = generate_request_id()
    start_time = time.time()
    
    logger.info(
        f"Operation started: {operation_name}",
        operation_name=operation_name,
        operation_id=operation_id,
        **context_data
    )
    
    try:
        yield operation_id
        duration = time.time() - start_time
        logger.info(
            f"Operation completed: {operation_name}",
            operation_name=operation_name,
            operation_id=operation_id,
            duration_seconds=round(duration, 4),
            success=True,
            **context_data
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Operation failed: {operation_name}",
            operation_name=operation_name,
            operation_id=operation_id,
            duration_seconds=round(duration, 4),
            success=False,
            error=str(e),
            error_type=type(e).__name__,
            **context_data
        )
        raise


class PerformanceLogger:
    """
    Helper class for logging performance metrics.
    """
    
    def __init__(self, logger=None):
        """
        Initialize performance logger.
        
        Args:
            logger: Logger instance (if None, creates a debug logger)
        """
        from app.core.logger import get_debug_logger
        self.logger = logger or get_debug_logger("performance", sublog="performance")
    
    def log_timing(
        self,
        operation: str,
        duration_ms: float,
        **extra_data
    ):
        """
        Log timing information for an operation.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            **extra_data: Additional data to log
        """
        self.logger.debug(
            f"Performance metric: {operation}",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **extra_data
        )
    
    def log_resource_usage(
        self,
        resource_type: str,
        usage: float,
        unit: str = "MB",
        **extra_data
    ):
        """
        Log resource usage information.
        
        Args:
            resource_type: Type of resource (e.g., "memory", "cpu")
            usage: Usage amount
            unit: Unit of measurement
            **extra_data: Additional data to log
        """
        self.logger.debug(
            f"Resource usage: {resource_type}",
            resource_type=resource_type,
            usage=usage,
            unit=unit,
            **extra_data
        )


def sanitize_log_data(data: Dict[str, Any], sensitive_keys: list = None) -> Dict[str, Any]:
    """
    Sanitize sensitive data from log entries.
    
    Args:
        data: Dictionary of log data
        sensitive_keys: List of keys to redact (default: common sensitive keys)
    
    Returns:
        Dictionary with sensitive data redacted
    
    Example:
        log_data = {"username": "john", "password": "secret123"}
        sanitized = sanitize_log_data(log_data)
        # Result: {"username": "john", "password": "***REDACTED***"}
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'passwd', 'pwd',
            'secret', 'token', 'api_key', 'apikey',
            'authorization', 'auth',
            'credit_card', 'ssn', 'social_security'
        ]
    
    sanitized = data.copy()
    
    for key in sanitized:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
    
    return sanitized

