#!/usr/bin/env bash
set -euo pipefail

uv sync --frozen --dev
npm ci
npm run build:css -- --watch=always &
npx esbuild frontend/viewer.js --bundle --minify --format=iife \
  --outfile=src/rignostic/web/static/js/viewer.bundle.js --watch=forever &
npx esbuild frontend/compare.js --bundle --minify --format=iife \
  --outfile=src/rignostic/web/static/js/compare.bundle.js --watch=forever &
npx esbuild frontend/landing.js --bundle --minify --format=iife \
  --outfile=src/rignostic/web/static/js/landing.bundle.js --watch=forever &

cleanup() {
  kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT INT TERM

exec uv run python -m rignostic.web
