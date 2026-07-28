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

# Create non-root user (ubuntu)
RUN groupadd -r ubuntu && useradd -r -g ubuntu -d /app -s /bin/bash ubuntu

# Set workdir
WORKDIR /app

# Copy dependencies từ builder stage
COPY --from=builder /install /usr/local

# Copy source code
COPY --chown=ubuntu:ubuntu . .

# Create logs directory
RUN mkdir -p /app/logs && chown -R ubuntu:ubuntu /app/logs

# Grant permissions for existing /data directory
RUN chown -R ubuntu:ubuntu /data && chmod 755 /data

# Switch to non-root user
USER ubuntu

# Expose port cho MCP Server (HF Spaces dùng port 8080)
EXPOSE 8080

# Healthcheck - kiểm tra MCP Server endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/status', timeout=5)" || exit 1

# Default command
CMD ["python", "server.py"]
