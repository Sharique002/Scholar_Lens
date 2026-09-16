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
python manage.py migrate --noinput

echo "==> Initializing admin and faculty accounts..."
python manage.py init_admin

echo "==> Build complete!"
