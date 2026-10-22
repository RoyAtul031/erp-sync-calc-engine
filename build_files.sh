#!/bin/bash
# Vercel Build Script for Django
echo "Building project dependencies..."
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
echo "Build complete."
