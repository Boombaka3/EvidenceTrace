#!/bin/sh
set -e

echo "Building frontend..."
if [ -d "/app/frontend" ]; then
    cd /app/frontend
    npm install --silent
    npm run build
    cd /app
    echo "Frontend built."
else
    echo "No frontend directory found, skipping build."
fi

echo "Running migrations..."
uv run python manage.py migrate_schemas --shared --noinput
uv run python manage.py migrate_schemas --noinput

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput

echo "Creating admin user..."
uv run python scripts/create_admin.py || true

exec "$@"
