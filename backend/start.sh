#!/bin/sh
set -e

echo "Doing alembic migrations..."
alembic upgrade head

echo "starting fastapi..."
exec fastapi run app/main.py --host 0.0.0.0 --port 8000
