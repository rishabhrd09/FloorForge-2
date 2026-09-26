#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ "$(uname -s)" = "Darwin" ] || { echo "Build this on macOS, not Linux or Windows." >&2; exit 1; }
./setup.sh
.venv/bin/python -m pip install -r requirements-packaging.txt
.venv/bin/python -m PyInstaller --clean --noconfirm packaging/FloorForge.spec
mkdir -p dist/dmg-stage
rm -rf dist/dmg-stage/FloorForge.app
cp -R dist/FloorForge.app dist/dmg-stage/
ln -sfn /Applications dist/dmg-stage/Applications
hdiutil create -volname FloorForge -srcfolder dist/dmg-stage -ov -format UDZO dist/FloorForge-0.2.0-unsigned.dmg
echo "Unsigned DMG built. Signing, notarisation and clean-machine acceptance are separate release gates."
