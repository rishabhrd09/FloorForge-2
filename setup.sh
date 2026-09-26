#!/usr/bin/env bash
set -euo pipefail

# This script is deliberately self-contained. It can be called from any
# directory and never installs packages into the user's global Python.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_DIR="$ROOT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
LOCK_FILE="$ROOT_DIR/requirements.lock.txt"
READY_FILE="$VENV_DIR/.floorforge-ready"

die() {
  printf 'FloorForge setup failed: %s\n' "$1" >&2
  exit 1
}

is_supported_python() {
  "$1" -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 14) else 1)' >/dev/null 2>&1
}

python_version() {
  "$1" -c 'import platform; print(platform.python_version())'
}

select_python() {
  local candidate found

  # An explicit executable is useful for CI and unusual Python installations.
  if [ -n "${FLOORFORGE_PYTHON:-}" ]; then
    candidate="$FLOORFORGE_PYTHON"
    if ! command -v "$candidate" >/dev/null 2>&1 && [ ! -x "$candidate" ]; then
      die "FLOORFORGE_PYTHON does not point to an executable: $candidate"
    fi
    if ! is_supported_python "$candidate"; then
      die "$candidate is Python $(python_version "$candidate" 2>/dev/null || printf 'unknown'); FloorForge requires Python 3.11, 3.12 or 3.13."
    fi
    printf '%s\n' "$candidate"
    return 0
  fi

  # Prefer an explicitly versioned executable. On macOS it is common for
  # python3 to point at a newer, unsupported version while python3.11 is
  # installed and available.
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && is_supported_python "$candidate"; then
      command -v "$candidate"
      return 0
    fi
  done

  # uv can install an isolated, supported Python without changing the system
  # Python. It is used only when no compatible interpreter is already present.
  if command -v uv >/dev/null 2>&1; then
    printf 'No supported system Python found. uv will install Python 3.13 locally.\n' >&2
    if uv python install 3.13 >/dev/null; then
      found="$(uv python find 3.13 2>/dev/null || true)"
      if [ -n "$found" ] && is_supported_python "$found"; then
        printf '%s\n' "$found"
        return 0
      fi
    fi
  fi

  die "No Python 3.11-3.13 interpreter was found. Install one, or install uv so setup can provision Python 3.13 automatically."
}

PYTHON="$(select_python)"
printf 'Using Python %s (%s)\n' "$(python_version "$PYTHON")" "$PYTHON"

if [ ! -f "$LOCK_FILE" ]; then
  die "Missing requirements.lock.txt in $ROOT_DIR"
fi

# Repair an old environment created with the wrong Python automatically.
if [ -x "$VENV_PYTHON" ] && ! is_supported_python "$VENV_PYTHON"; then
  printf 'Existing .venv uses an unsupported Python; recreating it with Python %s.\n' "$(python_version "$PYTHON")"
  "$PYTHON" -m venv --clear "$VENV_DIR" || die "Could not recreate $VENV_DIR"
elif [ ! -x "$VENV_PYTHON" ]; then
  "$PYTHON" -m venv "$VENV_DIR" || die "Could not create $VENV_DIR"
fi

pip_install() {
  if [ "$1" = 'offline' ] || [ -n "${FLOORFORGE_WHEELHOUSE:-}" ]; then
    if [ -n "${FLOORFORGE_WHEELHOUSE:-}" ]; then
      "$VENV_PYTHON" -m pip install --disable-pip-version-check --no-index --find-links "$FLOORFORGE_WHEELHOUSE" -r "$LOCK_FILE"
    else
      "$VENV_PYTHON" -m pip install --disable-pip-version-check --no-index -r "$LOCK_FILE"
    fi
  else
    "$VENV_PYTHON" -m pip install --disable-pip-version-check -r "$LOCK_FILE"
  fi
}

if [ -n "${FLOORFORGE_WHEELHOUSE:-}" ]; then
  [ -d "$FLOORFORGE_WHEELHOUSE" ] || die "FLOORFORGE_WHEELHOUSE is not a directory: $FLOORFORGE_WHEELHOUSE"
fi

printf 'Installing the pinned runtime dependencies into .venv...\n'
dependencies_ready=0
# Once setup has succeeded, retry the exact lock offline first. This keeps
# repeated setup runs usable without network access.
if [ -f "$READY_FILE" ] && pip_install offline >/dev/null 2>&1; then
  dependencies_ready=1
fi
if [ "$dependencies_ready" -eq 0 ] && ! pip_install online; then
  printf '%s\n' 'Check network access, Python version, free disk space or the offline wheelhouse.' >&2
  printf '%s\n' 'No global Python packages were changed. Re-run setup.sh after fixing the issue.' >&2
  exit 1
fi

printf 'Running the FloorForge smoke check...\n'
"$VENV_PYTHON" "$ROOT_DIR/scripts/smoke.py" || die "The installed runtime failed the smoke check"

LOCK_HASH="$("$VENV_PYTHON" -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$LOCK_FILE")"
PYTHON_VERSION="$("$VENV_PYTHON" -c 'import platform; print(platform.python_version())')"
{
  printf 'python=%s\n' "$PYTHON_VERSION"
  printf 'requirements_sha256=%s\n' "$LOCK_HASH"
} > "$READY_FILE"

# Keep the two user-facing launchers double-click/execute friendly after
# extracting an archive that did not preserve executable bits.
chmod +x "$ROOT_DIR/start.sh" "$ROOT_DIR/FloorForge.command" 2>/dev/null || true

printf '\nSetup complete. Run ./start.sh to open FloorForge Studio.\n'
