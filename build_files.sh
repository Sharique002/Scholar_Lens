#!/bin/bash
echo "==> Building Scholar Lens for Vercel..."
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput
echo "==> Vercel build complete!"
