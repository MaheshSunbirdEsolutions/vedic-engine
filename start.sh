#!/usr/bin/env bash
# Jyotish Lab (Next.js app + Python Vedic Engine) - Mac/Linux
set -e
cd "$(dirname "$0")"
command -v node >/dev/null || { echo "Node.js 20+ required: https://nodejs.org"; exit 1; }
./start-engine.sh &
ENGINE=$!
trap 'kill $ENGINE 2>/dev/null' EXIT
cd web
[ -d node_modules ] || npm install --no-audit --no-fund
npm run build
( sleep 3; (xdg-open http://localhost:3000 || open http://localhost:3000) >/dev/null 2>&1 ) &
npm start
