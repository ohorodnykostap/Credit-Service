#!/bin/bash
set -e

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

echo "Waiting for PostgreSQL on $DB_HOST:$DB_PORT..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "PostgreSQL is up!"

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi

if [ "$SEED_DATA" = "1" ]; then
  echo "Seeding data..."
  python -m app.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ${UVICORN_ARGS:-}