# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including GDAL/GEOS for GeoDjango
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    g++ \
    binutils \
    libproj-dev \
    libgdal-dev \
    gdal-bin \
    libgeos-dev \
    libgeos++-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*


# Set GDAL environment variables for the container
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Check system GDAL version to ensure compatibility
RUN echo "System GDAL version:" && gdal-config --version

# Install Python dependencies (GDAL will be installed separately)
RUN pip install --upgrade pip setuptools wheel

# Install GDAL Python bindings with exact version matching system libgdal (3.10.3)
# This must match the system libgdal version exactly
RUN pip install --no-cache-dir "GDAL==3.10.3"

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Create logs directory
RUN mkdir -p logs

# Expose port (fly.io will set this via PORT env var)
EXPOSE 8000

# Use a startup script
CMD ["/app/start.sh"]

