#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_DIR="$ROOT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
READY_FILE="$VENV_DIR/.floorforge-ready"
LOCK_FILE="$ROOT_DIR/requirements.lock.txt"

needs_setup=0
if [ ! -x "$VENV_PYTHON" ] || [ ! -f "$READY_FILE" ]; then
  needs_setup=1
else
  # Avoid starting an environment made for the wrong Python or an older lock.
  if ! "$VENV_PYTHON" -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 14) else 1)' >/dev/null 2>&1; then
    needs_setup=1
  elif ! "$VENV_PYTHON" -c 'import numpy, shapely, trimesh, ezdxf, reportlab, PIL, scipy, networkx, pyparsing, typing_extensions, fontTools, charset_normalizer' >/dev/null 2>&1; then
    needs_setup=1
  else
    expected_lock="$("$VENV_PYTHON" -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$LOCK_FILE")"
    if ! grep -Fqx "requirements_sha256=$expected_lock" "$READY_FILE"; then
      needs_setup=1
    fi
  fi
fi

if [ "$needs_setup" -eq 1 ]; then
  bash "$ROOT_DIR/setup.sh"
fi

exec "$VENV_PYTHON" -m floorforge serve "$@"
