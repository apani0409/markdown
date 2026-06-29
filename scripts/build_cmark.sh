#!/usr/bin/env bash
# Build the cmark C reference implementation at the pinned CommonMark spec
# version and expose its shared library for the ctypes-based adapter.
#
# Why build from source (spec §5): the reference oracle must match the chosen
# spec version (0.31.2). No pip-installable Python binding bundles cmark 0.31.2
# (paka.cmark -> 0.30.2, cmarkgfm -> 0.29.0.gfm.2), so we compile the exact tag.
#
# Output: vendor/cmark/build/src/libcmark.so.<ver>  +  the `cmark` CLI binary.
# Idempotent: re-running rebuilds in place.
set -euo pipefail

CMARK_VERSION="${CMARK_VERSION:-0.31.2}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="${ROOT}/vendor"
SRC="${VENDOR}/cmark"
TARBALL="${VENDOR}/cmark-${CMARK_VERSION}.tar.gz"
URL="https://github.com/commonmark/cmark/archive/refs/tags/${CMARK_VERSION}.tar.gz"

command -v cmake >/dev/null || { echo "ERROR: cmake not found" >&2; exit 1; }
command -v cc    >/dev/null || command -v gcc >/dev/null || { echo "ERROR: no C compiler" >&2; exit 1; }

mkdir -p "${VENDOR}"

if [[ ! -f "${TARBALL}" ]]; then
    echo ">> downloading cmark ${CMARK_VERSION}"
    # NOTE: in restricted network environments `git clone` may be blocked while
    # release tarballs over HTTPS are allowed; we use the tarball.
    curl -sSL -o "${TARBALL}" "${URL}"
fi

echo ">> extracting"
rm -rf "${SRC}"
tar xzf "${TARBALL}" -C "${VENDOR}"
mv "${VENDOR}/cmark-${CMARK_VERSION}" "${SRC}"

echo ">> configuring (BUILD_SHARED_LIBS=ON)"
cmake -S "${SRC}" -B "${SRC}/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMARK_TESTS=OFF \
    -DBUILD_SHARED_LIBS=ON >/dev/null

echo ">> building"
make -C "${SRC}/build" -j"$(nproc 2>/dev/null || echo 2)" >/dev/null

SO="$(find "${SRC}/build" -name 'libcmark.so*' -type f | head -1)"
BIN="${SRC}/build/src/cmark"
[[ -f "${SO}" ]] || { echo "ERROR: libcmark.so not produced" >&2; exit 1; }

echo ">> built:"
echo "   lib: ${SO}"
echo "   cli: ${BIN}"
"${BIN}" --version | head -1
