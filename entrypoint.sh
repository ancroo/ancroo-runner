#!/bin/bash
set -e

# Install plugin requirements at startup (builtin + user plugins)
for dir in /app/plugins /app/user-plugins; do
  for req in "$dir"/*/requirements.txt; do
    if [ -f "$req" ]; then
      echo "Installing requirements from $req"
      pip install --no-cache-dir --user -r "$req" 2>&1 | tail -1
    fi
  done
done

exec "$@"
