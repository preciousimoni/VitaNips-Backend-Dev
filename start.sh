#!/bin/bash
# Don't use set -e here - we want to continue even if some steps fail
set +e

# Wait for database to be ready (with shorter timeout)
echo "Waiting for database..."
python << END
import sys
import time
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

max_attempts = 10  # Reduced from 30 to 10 (20 seconds max)
attempt = 0

while attempt < max_attempts:
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("Database is ready!")
        break
    except Exception as e:
        attempt += 1
        if attempt >= max_attempts:
            print(f"WARNING: Database connection failed after {max_attempts} attempts: {e}")
            print("Continuing anyway - database may be available later")
            break  # Don't exit, continue with startup
        print(f"Waiting for database... (attempt {attempt}/{max_attempts})")
        time.sleep(2)
END

# Run migrations (non-blocking - don't fail if DB isn't ready)
echo "Running migrations..."
python manage.py migrate --noinput || echo "WARNING: Migrations failed, but continuing startup"

# Collect static files (if not already done in Dockerfile)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Start server - MUST listen on 0.0.0.0, not 127.0.0.1
echo "Starting server on 0.0.0.0:${PORT:-8000}..."
exec daphne -b 0.0.0.0 -p ${PORT:-8000} vitanips.asgi:application

