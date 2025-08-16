# Multi-stage build for noteparser
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    ffmpeg \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r noteparser && useradd -r -g noteparser noteparser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/noteparser/.local

# Copy application code
COPY --chown=noteparser:noteparser . .

# Install the package
RUN pip install -e .

# Set environment variables
ENV PATH=/home/noteparser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV NOTEPARSER_ENV=production

# Switch to non-root user
USER noteparser

# Expose ports
EXPOSE 5000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Default command
CMD ["noteparser", "web", "--host", "0.0.0.0", "--port", "5000"]