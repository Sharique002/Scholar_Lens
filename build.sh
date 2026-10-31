#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static assets..."
python manage.py collectstatic --noinput

echo "==> Running database migrations..."
python manage.py migrate --noinput || echo "Warning: Database migrations could not run during build (will be verified on startup)."

echo "==> Initializing default accounts..."
python manage.py init_admin || echo "Warning: init_admin could not run during build (will be verified on startup)."

echo "==> Build complete!"
