#!/usr/bin/env bash
# Retry pages with exponential backoff on 529 (overloaded) errors.
set -euo pipefail
cd "$(dirname "$0")/.."

PAGES=("$@")
if [[ ${#PAGES[@]} -eq 0 ]]; then
  PAGES=(7 11 38)
fi

for pg in "${PAGES[@]}"; do
  echo "==> Page $pg"
  delay=15
  for attempt in 1 2 3 4 5; do
    if .venv/bin/python scripts/extract_with_claude.py "$pg" --force 2>&1 | tee /tmp/retry_p${pg}.log | tail -2 | grep -q "ERROR"; then
      echo "  attempt $attempt: FAIL. Sleeping ${delay}s..."
      sleep "$delay"
      delay=$((delay * 2))
    else
      echo "  attempt $attempt: OK"
      break
    fi
  done
done
echo "Retries finished."
