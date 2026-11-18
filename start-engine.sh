#!/usr/bin/env bash
# Vedic Engine (Python API) - Mac/Linux
set -e
cd "$(dirname "$0")"
PY=$(command -v python3.12 || command -v python3.11 || command -v python3)
[ -x .venv/bin/python ] || "$PY" -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
exec .venv/bin/python -m uvicorn vedic_engine.api:app --host 127.0.0.1 --port 8000
