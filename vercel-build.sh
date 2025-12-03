#!/bin/bash
# Vercel build script - Skip mise and use Vercel's Python runtime

# Skip mise if it's trying to run
export MISE_SKIP=1
export SKIP_MISE=1

# Use Vercel's Python
export PYTHON_VERSION=3.11

# Install dependencies
pip install -r requirements.txt

# Collect static files (if needed)
python manage.py collectstatic --noinput || true

echo "Build completed successfully"

