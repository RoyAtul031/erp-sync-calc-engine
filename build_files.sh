#!/bin/bash
# Enterprise Deployment Build Script
set -e

echo "=== 1/4 Installing dependencies ==="
pip install -r requirements.txt

echo "=== 2/4 Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== 3/4 Running database migrations ==="
python manage.py migrate --noinput

echo "=== 4/4 Seeding enterprise ESG reference data ==="
python manage.py seed_enterprise_data

echo "=== Build completed successfully! ==="
