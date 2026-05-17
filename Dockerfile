# ============================================
# OpenGov AI Assistant - Dockerfile
# Multi-stage build for production deployment
# ============================================

# Stage 1: Build and install Python dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create data directories
RUN mkdir -p /app/backend/data/FR \
    && mkdir -p /app/backend/data/Procurement \
    && mkdir -p /app/backend/data/ECode \
    && mkdir -p /app/backend/vector_db

# Create .env file from example if not exists
RUN if [ ! -f /app/backend/.env ]; then \
    cp /app/backend/.env.example /app/backend/.env; \
    fi

# Set working directory
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]