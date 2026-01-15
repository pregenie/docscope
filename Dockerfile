# Multi-stage build for DocScope
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 docscope && \
    mkdir -p /app /data /config && \
    chown -R docscope:docscope /app /data /config

# Copy Python packages from builder
COPY --from=builder /root/.local /home/docscope/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=docscope:docscope . .

# Switch to non-root user
USER docscope

# Add user's local bin to PATH
ENV PATH=/home/docscope/.local/bin:$PATH

# Environment variables
ENV DOCSCOPE_DATA_DIR=/data \
    DOCSCOPE_CONFIG_DIR=/config \
    DOCSCOPE_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Volume mounts
VOLUME ["/data", "/config"]

# Default command
CMD ["python", "-m", "docscope", "serve", "--host", "0.0.0.0", "--port", "8000"]