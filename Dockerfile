# MCP Programming Support Server - Production Dockerfile
# Multi-stage build để tối ưu kích thước image

# =============================================================================
# STAGE 1: Builder - Cài đặt dependencies
# =============================================================================
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /build

# Copy requirements first để tối ưu layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --prefix=/install -r requirements.txt


# =============================================================================
# STAGE 2: Production - Image cuối cùng nhỏ gọn
# =============================================================================
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app:${PATH}"

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser -d /app -s /bin/bash mcpuser

# Set workdir
WORKDIR /app

# Copy dependencies từ builder stage
COPY --from=builder /install /usr/local

# Copy source code
COPY --chown=mcpuser:mcpuser . .

# Create logs directory
RUN mkdir -p /app/logs && chown -R mcpuser:mcpuser /app/logs

# Switch to non-root user
USER mcpuser

# Expose ports: 7860 cho MCP Server (SSE), 8080 cho Dashboard
EXPOSE 7860
EXPOSE 8080

# Healthcheck - kiểm tra Dashboard endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/status', timeout=5)" || exit 1

# Default command
CMD ["python", "server.py"]
