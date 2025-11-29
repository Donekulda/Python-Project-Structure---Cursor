# Python-Project-Structure---Cursor

A well-structured Python project template with comprehensive configuration management and advanced structured logging capabilities.

## Features

- **Structured Logging**: Advanced logging system using `structlog` with JSON output for log aggregation
- **Colored Console Output**: Beautiful colored console logs for better development experience
- **Multiple Log Types**: Separate logs for Error, App, Debug, and Security events
- **Daily Log Rotation**: Automatic rotation with archived logs
- **Graylog Compatible**: JSON-formatted logs ready for ingestion by Graylog or other systems
- **Separate Log Levels**: Different log levels for console and file outputs
- **Configuration Management**: Centralized configuration using Pydantic Settings
- **Environment Support**: Easy configuration via environment variables

## Quick Start

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Usage

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

### Running the Application

```bash
# Using the startup script
./startup.sh

# Or directly with Python
python -m app.main
```

### Testing the Logging System

```bash
python test_logging_system.py
```

This will generate example logs in the `logs/` directory demonstrating all logging features.

## Documentation

For comprehensive documentation on the logging system, see [docs/logging.md](docs/logging.md).

## Project Structure

See [AGENTS.md](AGENTS.md) for detailed project structure and guidelines.
