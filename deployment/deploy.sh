#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$(pwd)}"
SERVICE_NAME="${SERVICE_NAME:-simaset}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8001/login}"

cd "$APP_DIR"
echo "Running SIMASET deploy script with retrying health check"

if [ ! -f ".env" ]; then
  echo "Missing .env in $APP_DIR" >&2
  exit 1
fi

git fetch origin main
git reset --hard origin/main

if [ ! -d "venv" ]; then
  "$PYTHON_BIN" -m venv venv
fi

venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

mkdir -p exports app/static/qrcodes

venv/bin/flask db upgrade

sudo systemctl restart "$SERVICE_NAME"
sudo systemctl --no-pager --full status "$SERVICE_NAME"

for attempt in $(seq 1 30); do
  if curl --fail --head --max-time 5 "$HEALTHCHECK_URL"; then
    echo "Health check passed on attempt $attempt"
    exit 0
  fi

  echo "Health check attempt $attempt failed, retrying..."
  sleep 1
done

echo "Health check failed after 30 attempts: $HEALTHCHECK_URL" >&2
sudo journalctl -u "$SERVICE_NAME" -n 80 --no-pager
exit 1
