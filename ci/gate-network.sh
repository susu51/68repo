#!/bin/bash
set -euo pipefail

PATTERN='http://localhost:8001|REACT_APP_|apiClient\.js'
if grep -RInE "$PATTERN" --exclude-dir=node_modules --exclude-dir=.git /app/frontend; then
  echo "❌ CI FAIL: Local URL / REACT_APP_ / apiClient.js found"
  exit 1
fi
echo "✅ Network Gate PASS"