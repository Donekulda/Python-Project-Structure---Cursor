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


# Create non-root user/group with explicit UID/GID 666
RUN groupadd -g 696 appgroup \
    && useradd --no-log-init -u 696 -g 696 -m -s /usr/sbin/nologin appuser

# Install Python dependencies
COPY --chown=696:696 requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application code (no development files)
COPY --chown=696:696 app/ ./app/

# Copy startup script
COPY --chown=696:696 startup.sh /startup.sh