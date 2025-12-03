#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
python << END
import sys
import time
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

max_attempts = 30
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
            print(f"Database connection failed after {max_attempts} attempts: {e}")
            sys.exit(1)
        print(f"Waiting for database... (attempt {attempt}/{max_attempts})")
        time.sleep(2)
END

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (if not already done in Dockerfile)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Start server
echo "Starting server..."
exec daphne -b 0.0.0.0 -p ${PORT:-8000} vitanips.asgi:application

