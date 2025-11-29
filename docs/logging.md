# Structured Logging System Documentation

## Overview

This project uses a comprehensive structured logging system built with `structlog` and `colorlog` that provides:

- **Structured logging**: All logs are structured with key-value pairs for easy parsing and analysis
- **Colored console output**: Console logs are colorized for better readability during development
- **Separate log levels**: Different log levels for console and file outputs
- **Multiple log types**: Error, App, Debug, and Security logs with separate files
- **Daily log rotation**: Automatic rotation with archived logs
- **Graylog compatibility**: JSON-formatted file logs ready for ingestion by Graylog or other log aggregation systems

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Log Types](#log-types)
- [Usage Examples](#usage-examples)
- [Structured Logging Best Practices](#structured-logging-best-practices)
- [Log File Structure](#log-file-structure)
- [Helper Utilities](#helper-utilities)
- [Graylog Integration](#graylog-integration)

## Quick Start

### Basic Usage

```python
from app.core.logger import get_logger

# Get a logger instance
logger = get_logger(__name__)

# Simple logging
logger.info("Application started")

# Structured logging with context
logger.info(
    "User logged in",
    user_id=123,
    username="john.doe",
    ip_address="192.168.1.1"
)
```

### Initialize Logging

The logging system is automatically initialized on first use, but you can explicitly initialize it in your application's main entry point:

```python
from app.core.logger import setup_logging

# Initialize logging system
setup_logging()
```

## Configuration

Logging is configured through `app/core/config.py` with the following settings:

### Environment Variables

Create a `.env` file in your project root:

```env
# Console log level (what appears in terminal)
CONSOLE_LOG_LEVEL=INFO

# File log level (what gets written to log files)
FILE_LOG_LEVEL=DEBUG

# Log directory
LOG_DIR=logs

# Log rotation check interval (seconds)
LOG_ROTATION_TIMEOUT=300
```

### Configuration Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `CONSOLE_LOG_LEVEL` | `INFO` | Log level for console output (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `FILE_LOG_LEVEL` | `DEBUG` | Log level for file output (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_DIR` | `logs` | Directory where log files are stored |
| `LOG_ROTATION_TIMEOUT` | `300` | Interval in seconds for checking log rotation (5 minutes) |

### Log Levels

- **DEBUG**: Detailed information, typically of interest only when diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: An indication that something unexpected happened, but the application is still working
- **ERROR**: A more serious problem, the software has not been able to perform some function
- **CRITICAL**: A very serious error, the program itself may be unable to continue running

## Log Types

The logging system supports four types of logs, each stored in its own subdirectory:

### 1. Error Logs (`logs/error/`)

**Purpose**: Captures all ERROR and CRITICAL level messages from the entire application.

**File**: `logs/error/error.log`

**Usage**:
```python
from app.core.logger import get_error_logger

error_logger = get_error_logger(__name__)
error_logger.error(
    "Database connection failed",
    db_host="localhost",
    db_port=5432,
    error_code="CONNECTION_TIMEOUT"
)
```

### 2. App Logs (`logs/app/`)

**Purpose**: General application logs (INFO, WARNING, and below ERROR).

**File**: `logs/app/app.log`

**Usage**:
```python
from app.core.logger import get_app_logger

app_logger = get_app_logger(__name__)
app_logger.info(
    "User registration completed",
    user_id=456,
    registration_method="email"
)
```

### 3. Debug Logs (`logs/debug/`)

**Purpose**: Detailed debug information with optional sublog files.

**Files**: 
- `logs/debug/debug.log` (default)
- `logs/debug/{sublog}.log` (when sublog is specified)

**Usage**:
```python
from app.core.logger import get_debug_logger

# Default debug.log
debug_logger = get_debug_logger(__name__)
debug_logger.debug("Processing started", task_id="task_123")

# Custom sublog: logs/debug/api.log
api_debug_logger = get_debug_logger(__name__, sublog="api")
api_debug_logger.debug(
    "API request received",
    endpoint="/users",
    method="GET",
    query_params={"page": 1}
)

# Custom sublog: logs/debug/database.log
db_debug_logger = get_debug_logger(__name__, sublog="database")
db_debug_logger.debug(
    "Database query executed",
    query="SELECT * FROM users",
    execution_time_ms=45.2
)
```

### 4. Security Logs (`logs/security/`)

**Purpose**: Security-related events like authentication, authorization, and security incidents.

**File**: `logs/security/security.log` (created only when first used)

**Usage**:
```python
from app.core.logger import get_security_logger

security_logger = get_security_logger(__name__)
security_logger.info(
    "Login attempt",
    username="john.doe",
    ip_address="192.168.1.1",
    success=True,
    authentication_method="password"
)

security_logger.warning(
    "Failed login attempt",
    username="attacker",
    ip_address="10.0.0.1",
    success=False,
    reason="invalid_password",
    attempts_count=3
)
```

## Usage Examples

### Basic Logging

```python
from app.core.logger import get_logger

logger = get_logger(__name__)

# Different log levels
logger.debug("Debugging information", variable_value=42)
logger.info("Informational message", status="running")
logger.warning("Warning message", disk_usage_percent=85)
logger.error("Error occurred", error_code="ERR_001")
logger.critical("Critical failure", system="database")

# Exception logging with traceback
try:
    result = 1 / 0
except Exception:
    logger.exception("Division by zero error", operation="calculate")
```

### Structured Logging with Context

```python
from app.core.logger import get_logger

logger = get_logger(__name__)

# Add rich context to logs
logger.info(
    "Order processed",
    order_id="ORD-12345",
    customer_id=789,
    total_amount=149.99,
    currency="USD",
    items_count=3,
    processing_time_ms=234
)
```

### Using Sublog Files

```python
from app.core.logger import get_debug_logger

# Create separate debug logs for different subsystems
middleware_logger = get_debug_logger(__name__, sublog="middleware")
middleware_logger.debug(
    "Request middleware executed",
    middleware="AuthMiddleware",
    execution_time_ms=12.5
)

cache_logger = get_debug_logger(__name__, sublog="cache")
cache_logger.debug(
    "Cache hit",
    key="user:123",
    ttl_seconds=300
)
```

### Using Helper Functions

```python
from app.core.logger import get_logger
from app.utils.logging_helpers import (
    log_execution_time,
    log_function_call,
    log_operation,
    RequestLogger,
    SecurityLogger
)

# Decorator for timing functions
@log_execution_time()
def process_data(data):
    # Processing logic
    return result

# Decorator for logging function calls
@log_function_call(log_args=True, log_result=True)
def calculate_total(price, quantity):
    return price * quantity

# Context manager for operations
with log_operation("data_migration", version="1.2.0"):
    migrate_data()

# Request logging helper
request_logger = RequestLogger()
request_logger.log_request(
    method="POST",
    path="/api/users",
    status_code=201,
    duration_ms=45.3,
    user_id=123
)

# Security logging helper
security_logger = SecurityLogger()
security_logger.log_authentication_attempt(
    username="john.doe",
    success=True,
    ip_address="192.168.1.1"
)
```

## Structured Logging Best Practices

### 1. Use Descriptive Messages

```python
# Good
logger.info("User authentication successful", user_id=123, method="oauth")

# Bad
logger.info("Success")
```

### 2. Add Relevant Context

```python
# Good
logger.error(
    "Payment processing failed",
    order_id="ORD-123",
    payment_method="credit_card",
    amount=99.99,
    error_code="PAYMENT_DECLINED"
)

# Bad
logger.error("Payment failed")
```

### 3. Use Consistent Key Names

```python
# Use snake_case for consistency
logger.info("Request processed", user_id=123, request_id="req-456")

# Avoid inconsistent naming
logger.info("Request processed", userId=123, RequestID="req-456")
```

### 4. Don't Log Sensitive Information

```python
from app.utils.logging_helpers import sanitize_log_data

# Good - sanitize sensitive data
user_data = {"username": "john", "password": "secret123"}
sanitized = sanitize_log_data(user_data)
logger.info("User created", **sanitized)
# Output: {"username": "john", "password": "***REDACTED***"}

# Bad - logging sensitive data
logger.info("User created", username="john", password="secret123")
```

### 5. Use Appropriate Log Levels

```python
# DEBUG - Detailed diagnostic information
logger.debug("Cache lookup", key="user:123", found=True)

# INFO - General informational messages
logger.info("Application started", version="1.0.0")

# WARNING - Potentially harmful situations
logger.warning("Rate limit approaching", current=950, limit=1000)

# ERROR - Error events that might still allow the app to continue
logger.error("Failed to send email", recipient="user@example.com")

# CRITICAL - Severe error events that might cause the app to abort
logger.critical("Database connection lost", retries_exhausted=True)
```

### 6. Include Timing Information

```python
import time

start = time.time()
process_data()
duration = time.time() - start

logger.info(
    "Data processing completed",
    records_processed=1000,
    duration_seconds=duration
)
```

### 7. Use Exceptions Appropriately

```python
try:
    risky_operation()
except Exception as e:
    # Use .exception() to include traceback
    logger.exception(
        "Operation failed",
        operation="risky_operation",
        error_type=type(e).__name__
    )
```

## Log File Structure

```
logs/
├── error/
│   ├── error.log                    # Current error log
│   └── error-2025-11-28.hist.log    # Archived error log
├── app/
│   ├── app.log                      # Current app log
│   └── app-2025-11-28.hist.log      # Archived app log
├── debug/
│   ├── debug.log                    # Default debug log
│   ├── api.log                      # API-specific debug log
│   ├── database.log                 # Database-specific debug log
│   ├── debug-2025-11-28.hist.log    # Archived debug log
│   └── api-2025-11-28.hist.log      # Archived API debug log
└── security/
    ├── security.log                 # Current security log (created on first use)
    └── security-2025-11-28.hist.log # Archived security log
```

### Log Rotation

- Logs are automatically rotated daily at midnight
- Current logs: `{type}.log`
- Archived logs: `{type}-YYYY-MM-DD.hist.log`
- A background thread checks for date changes every 5 minutes (configurable)

### Manual Log Rotation

```python
from app.core.logger import force_log_rotation

# Force immediate log rotation check
rotated = force_log_rotation()
if rotated:
    print("Logs were rotated")
```

## Console Output

Console logs are colorized for better readability:

- **DEBUG**: Cyan
- **INFO**: Green
- **WARNING**: Yellow
- **ERROR**: Red
- **CRITICAL**: Red with white background

Console format:
```
2025-11-29 10:30:45 | INFO     | app.main | Application started
```

## File Output

File logs are in JSON format for easy parsing and ingestion by log aggregation systems:

```json
{
  "event": "User logged in",
  "user_id": 123,
  "username": "john.doe",
  "ip_address": "192.168.1.1",
  "timestamp": "2025-11-29T10:30:45.123456Z",
  "level": "info",
  "logger": "app.auth"
}
```

## Helper Utilities

### Execution Time Logging

```python
from app.utils.logging_helpers import log_execution_time

@log_execution_time(log_level="debug")
def expensive_operation():
    # ... operation ...
    pass
```

### Function Call Logging

```python
from app.utils.logging_helpers import log_function_call

@log_function_call(log_args=True, log_result=True)
def calculate(x, y):
    return x + y
```

### Operation Context Manager

```python
from app.utils.logging_helpers import log_operation

with log_operation("database_backup", database="production"):
    backup_database()
```

### Request Logging

```python
from app.utils.logging_helpers import RequestLogger

request_logger = RequestLogger()
request_logger.log_request(
    method="GET",
    path="/api/users/123",
    status_code=200,
    duration_ms=23.4,
    cache_hit=True
)
```

### Security Event Logging

```python
from app.utils.logging_helpers import SecurityLogger

security = SecurityLogger()

# Authentication
security.log_authentication_attempt(
    username="john.doe",
    success=True,
    ip_address="192.168.1.1"
)

# Authorization
security.log_authorization_check(
    user="john.doe",
    resource="admin_panel",
    action="access",
    allowed=False
)

# Generic security event
security.log_security_event(
    event_type="suspicious_activity",
    severity="warning",
    ip_address="10.0.0.1",
    reason="multiple_failed_attempts"
)
```

### Performance Logging

```python
from app.utils.logging_helpers import PerformanceLogger

perf_logger = PerformanceLogger()

perf_logger.log_timing(
    operation="database_query",
    duration_ms=45.2,
    query_type="SELECT"
)

perf_logger.log_resource_usage(
    resource_type="memory",
    usage=512.5,
    unit="MB",
    process="worker_1"
)
```

### Data Sanitization

```python
from app.utils.logging_helpers import sanitize_log_data

sensitive_data = {
    "username": "john",
    "password": "secret123",
    "api_key": "abc-def-ghi"
}

safe_data = sanitize_log_data(sensitive_data)
logger.info("User data", **safe_data)
# Output: {"username": "john", "password": "***REDACTED***", "api_key": "***REDACTED***"}
```

## Graylog Integration

The logging system produces JSON-formatted logs that are compatible with Graylog and other log aggregation systems.

### Log Format

Each log entry is a JSON object with the following structure:

```json
{
  "event": "Human-readable message",
  "timestamp": "2025-11-29T10:30:45.123456Z",
  "level": "info",
  "logger": "app.module.name",
  "key1": "value1",
  "key2": "value2"
}
```

### Graylog Configuration

1. **File Input**: Configure Graylog to read log files from the `logs/` directory
2. **Field Extraction**: JSON fields are automatically extracted
3. **Timestamp Parsing**: Use the `timestamp` field for event timing
4. **Filtering**: Create streams based on `level`, `logger`, or custom fields

### Example Graylog Queries

```
# All errors from the last hour
level:error AND timestamp:[now-1h TO now]

# Authentication failures
event:"Authentication failed" AND success:false

# Slow API requests
http_path:* AND duration_ms:>1000

# Security events from specific IP
logger:security AND ip_address:"192.168.1.1"
```

### Best Practices for Graylog

1. **Consistent Field Names**: Use consistent naming across your application
2. **Structured Data**: Always use key-value pairs instead of concatenating strings
3. **Include Context**: Add relevant IDs (user_id, request_id, etc.) to enable correlation
4. **Use Appropriate Types**: Numbers as numbers, booleans as booleans
5. **Set Up Alerts**: Create Graylog alerts for critical errors and security events

## Troubleshooting

### Logs Not Appearing

1. Check that logging is initialized: `setup_logging()` should be called
2. Verify log levels: Console and file log levels must allow the message level
3. Check directory permissions: Ensure the application can write to the `logs/` directory

### Performance Concerns

1. Adjust `LOG_ROTATION_TIMEOUT` to reduce rotation checks
2. Set `FILE_LOG_LEVEL` to INFO or higher in production
3. Use sublog files to separate high-volume debug logs

### Log Files Growing Too Large

1. Implement log file cleanup (see example implementations)
2. Configure external log rotation (logrotate on Linux)
3. Set up log forwarding to a centralized system and clean up local files

## Migration from Standard Logging

If you're migrating from Python's standard logging:

```python
# Old way
import logging
logger = logging.getLogger(__name__)
logger.info("User logged in: %s", username)

# New way
from app.core.logger import get_logger
logger = get_logger(__name__)
logger.info("User logged in", username=username)
```

Key differences:
- Use keyword arguments instead of string formatting
- No need to call `logging.basicConfig()`
- Automatic log rotation and structuring

## Additional Resources

- [structlog documentation](https://www.structlog.org/)
- [Graylog documentation](https://docs.graylog.org/)
- [Python logging documentation](https://docs.python.org/3/library/logging.html)

## Support

For issues or questions about the logging system:
1. Check this documentation
2. Review the example implementations in `examples/`
3. Examine the source code in `app/core/logger.py`

