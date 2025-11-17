# Flexible build with PUID/PGID support for easier file permissions
# For maximum security, use Dockerfile.distroless instead
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv (fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy requirements and install Python dependencies with uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY gmail-fetcher.py /app/

# Create default user (can be overridden with PUID/PGID)
ARG PUID=65532
ARG PGID=65532

# Create entrypoint script that handles user creation
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Default to non-root user\n\
PUID=${PUID:-65532}\n\
PGID=${PGID:-65532}\n\
\n\
# Create group if it doesn'\''t exist\n\
if ! getent group $PGID > /dev/null 2>&1; then\n\
    groupadd -g $PGID gmailfetcher 2>/dev/null || true\n\
fi\n\
\n\
# Create user if it doesn'\''t exist\n\
if ! getent passwd $PUID > /dev/null 2>&1; then\n\
    useradd -u $PUID -g $PGID -M -s /bin/bash gmailfetcher 2>/dev/null || true\n\
fi\n\
\n\
# Ensure data directory has correct ownership\n\
if [ -d /data ]; then\n\
    chown -R $PUID:$PGID /data 2>/dev/null || true\n\
fi\n\
\n\
# Execute command as the specified user\n\
exec gosu $PUID:$PGID python3 /app/gmail-fetcher.py "$@"\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/data \
    PUID=65532 \
    PGID=65532

# Create data directory
RUN mkdir -p /data && chmod 755 /data

# Volume for data
VOLUME ["/data"]

# Labels
LABEL org.opencontainers.image.title="Gmail Fetcher (Flexible)" \
      org.opencontainers.image.description="Secure local Gmail archiving with PUID/PGID support" \
      org.opencontainers.image.authors="Built with Claude Code" \
      security.non-root="true" \
      security.puid-pgid="true"

# Use entrypoint for user switching
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["--dash"]
