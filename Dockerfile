FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user/group with explicit UID/GID 696
RUN groupadd -g 696 appgroup \
    && useradd --no-log-init -u 696 -g 696 -m -s /usr/sbin/nologin appuser

# Install Python dependencies
COPY --chown=696:696 requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=696:696 app/ ./app/

# Copy startup script and make it executable
COPY --chown=696:696 startup.sh /startup.sh
RUN chmod +x /startup.sh

# Development target
FROM base AS development

# Install development and testing dependencies
RUN pip install --no-cache-dir \
    pytest>=7.4.0 \
    pytest-cov>=4.1.0 \
    pytest-asyncio>=0.21.0 \
    pytest-mock>=3.11.1

# Copy tests folder
COPY --chown=696:696 tests/ ./tests/

# Switch to non-root user
USER appuser

# Production target
FROM base AS production

# Switch to non-root user
USER appuser

# Production target inherits from base (no additional dependencies or test files)
# This keeps the production image minimal and secure