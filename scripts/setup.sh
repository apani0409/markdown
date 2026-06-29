#!/usr/bin/env bash
# One-command environment setup for cm-difftest.
#   1. create a virtualenv (.venv)
#   2. install pinned dependencies
#   3. build the cmark 0.31.2 reference (shared lib for the ctypes adapter)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

PY="${PYTHON:-python3}"

echo ">> creating venv"
"${PY}" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo ">> installing dependencies"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e ".[reference,fuzz,dev]"

echo ">> building cmark reference"
bash scripts/build_cmark.sh

echo ">> done. activate with: source .venv/bin/activate"
