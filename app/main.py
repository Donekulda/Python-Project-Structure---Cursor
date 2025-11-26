from app.core.config import settings  # Import settings for CORS configuration

if __name__ == "__main__":
    print(settings.APP_NAME)
    print(settings.APP_VERSION)
    print(settings.DEBUG)
    print(settings.ENVIRONMENT)