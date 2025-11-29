from app.core.config import settings
from app.core.logger import setup_logging, get_logger


def main():
    """Main application entry point."""
    # Initialize logging system
    setup_logging()
    
    # Get logger for main module
    logger = get_logger(__name__)
    
    # Log application startup
    print("=" * 50)
    print(f"Application: {settings.APP_NAME}")
    print(f"Version: {settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Console Log Level: {settings.CONSOLE_LOG_LEVEL}")
    print(f"File Log Level: {settings.FILE_LOG_LEVEL}")
    print(f"Log Directory: {settings.LOG_DIR}")
    print(f"API Host: {settings.API_HOST}")
    print(f"API Port: {settings.API_PORT}")
    print("=" * 50)
    
    # Log structured startup information
    logger.info(
        "Application started",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        debug_mode=settings.DEBUG,
        console_log_level=settings.CONSOLE_LOG_LEVEL,
        file_log_level=settings.FILE_LOG_LEVEL
    )
    
    # Your application code here
    logger.info("Application is running")


if __name__ == "__main__":
    main()