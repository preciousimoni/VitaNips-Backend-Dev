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
RUN GDAL_VERSION=$(gdal-config --version) && \
    echo "System GDAL version: $GDAL_VERSION" && \
    echo "$GDAL_VERSION" > /tmp/gdal_version.txt

# Upgrade pip and build tools
RUN pip install --upgrade pip setuptools wheel

# Install GDAL Python bindings FIRST with exact version matching system libgdal
# Read the version from the file we saved
RUN GDAL_VERSION=$(cat /tmp/gdal_version.txt) && \
    echo "Installing GDAL Python bindings version: $GDAL_VERSION" && \
    pip install --no-cache-dir "GDAL==${GDAL_VERSION}"

# Verify GDAL installation
RUN python -c "import osgeo; print(f'GDAL Python version: {osgeo.__version__}')" || true

# Create a constraints file to prevent GDAL from being upgraded or changed
RUN GDAL_VERSION=$(cat /tmp/gdal_version.txt) && \
    echo "GDAL==${GDAL_VERSION}" > /tmp/constraints.txt && \
    echo "Constraints file created with GDAL==${GDAL_VERSION}"

# Install remaining Python dependencies with constraint to keep GDAL at the system version
# The constraint file ensures GDAL won't be upgraded even if a dependency requests a newer version
RUN pip install --no-cache-dir -c /tmp/constraints.txt -r requirements.txt && \
    python -c "from osgeo import gdal; print(f'Final GDAL version check: {gdal.__version__}')" || true

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

