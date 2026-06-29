#!/usr/bin/env bash
# Idempotent environment bootstrap, safe to run on every session start.
#   - create .venv and install the package (editable, with extras) if missing
#   - build the cmark 0.31.2 reference shared lib if missing
# Never fails the session: on error it warns and exits 0.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}" || exit 0

warn() { echo "[bootstrap] $*" >&2; }

# 1. venv + deps
if [[ ! -x ".venv/bin/python" ]]; then
    warn "creating .venv and installing dependencies..."
    python3 -m venv .venv \
      && .venv/bin/python -m pip install --quiet --upgrade pip \
      && .venv/bin/python -m pip install --quiet -e ".[reference,fuzz,dev]" \
      || warn "dependency install failed (continuing)"
fi

# 2. cmark reference
if ! ls vendor/cmark/build/src/libcmark.so* >/dev/null 2>&1; then
    warn "building cmark 0.31.2 reference..."
    bash scripts/build_cmark.sh >/dev/null 2>&1 || warn "cmark build failed (run scripts/build_cmark.sh manually)"
fi

warn "ready."
exit 0
