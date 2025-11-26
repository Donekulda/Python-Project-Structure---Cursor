#!/bin/bash
set -euo pipefail

# Log directories are created in Dockerfile with proper ownership
# Just verify they exist (they should)
if [ ! -d "/logs" ]; then
    echo "WARNING: /logs directory not found!"
fi

# Execute the passed command as the current user (appuser in the image)
exec "$@"