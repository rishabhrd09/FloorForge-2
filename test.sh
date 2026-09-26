#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then ./setup.sh; fi
.venv/bin/python -m pip install -r requirements-dev.lock.txt
.venv/bin/python -m pytest -q --junitxml=evidence/local-pytest.xml
