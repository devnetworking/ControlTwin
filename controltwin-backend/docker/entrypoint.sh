#!/bin/bash
set -e

echo "Waiting for database..."
python /app/scripts/wait_for_db.py

echo "Running migrations..."
alembic -c /app/alembic.ini upgrade head

echo "Starting ControlTwin API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload