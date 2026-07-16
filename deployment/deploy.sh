#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$(pwd)}"
SERVICE_NAME="${SERVICE_NAME:-simaset}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$APP_DIR"

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
