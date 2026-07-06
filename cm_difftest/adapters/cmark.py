"""Adapter for the cmark C reference, bound in-process via ctypes (spec §7.1).

This is the ground-truth oracle. We build cmark from source at the pinned spec
version (0.31.2) — no pip binding ships that version — and call
``cmark_markdown_to_html`` directly. See ``scripts/build_cmark.sh``.

Modes (spec §6):
* RAW  -> ``CMARK_OPT_UNSAFE``: raw HTML and dangerous URLs pass through. This is
  what matches ``spec.txt``'s expected output (verified: 652/652).
* SAFE -> default options (0): raw HTML becomes ``<!-- raw HTML omitted -->`` and
  dangerous links are blanked.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import glob
import os
from pathlib import Path

from cm_difftest.adapters.base import Adapter, AdapterError, Mode, Provenance

__all__ = ["CmarkAdapter", "find_libcmark"]

# cmark option bit flags (from cmark.h).
CMARK_OPT_DEFAULT = 0
CMARK_OPT_UNSAFE = 1 << 17


def _repo_root() -> Path:
    # cm_difftest/adapters/cmark.py -> repo root is three parents up.
    return Path(__file__).resolve().parents[2]


def find_libcmark() -> str:
    """Locate the built ``libcmark`` shared library.

    Search order: ``$CM_DIFFTEST_LIBCMARK`` -> the vendored build -> system.
    Raises :class:`AdapterError` with a remediation hint if not found.
    """
    env = os.environ.get("CM_DIFFTEST_LIBCMARK")
    if env:
        if not os.path.exists(env):
            raise AdapterError(f"CM_DIFFTEST_LIBCMARK points at a missing file: {env}")
        return env

    vendored = sorted(
        glob.glob(str(_repo_root() / "vendor/cmark/build/src/libcmark.so*"))
    )
    if vendored:
        return vendored[-1]

    system = ctypes.util.find_library("cmark")
    if system:
        return system

    raise AdapterError(
        "libcmark not found. Build the reference with `bash scripts/build_cmark.sh` "
        "or set CM_DIFFTEST_LIBCMARK to a libcmark shared library."
    )


class CmarkAdapter(Adapter):
    """In-process ctypes binding to cmark's ``cmark_markdown_to_html``."""

    name = "cmark"
    is_reference = True

    def __init__(self, lib_path: str | None = None) -> None:
        self._lib_path = lib_path or find_libcmark()
        lib = ctypes.CDLL(self._lib_path)

        # char *cmark_markdown_to_html(const char *text, size_t len, int options)
        # Return a raw pointer (not c_char_p) so we can free it ourselves.
        self._render_fn = lib.cmark_markdown_to_html
        self._render_fn.restype = ctypes.c_void_p
        self._render_fn.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]

        # const char *cmark_version_string(void)
        self._version_fn = lib.cmark_version_string
        self._version_fn.restype = ctypes.c_char_p
        self._version_fn.argtypes = []

        # Free cmark's malloc'd output via libc free (default allocator).
        libc = ctypes.CDLL(None)
        self._free = libc.free
        self._free.argtypes = [ctypes.c_void_p]
        self._free.restype = None

        self._version = self._version_fn().decode("ascii")

    def render(self, markdown: str, *, mode: Mode = Mode.RAW) -> str:
        opts = CMARK_OPT_UNSAFE if mode is Mode.RAW else CMARK_OPT_DEFAULT
        data = markdown.encode("utf-8")
        ptr = self._render_fn(data, len(data), opts)
        if not ptr:
            raise AdapterError("cmark_markdown_to_html returned NULL")
        try:
            return ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
        finally:
            self._free(ptr)

    def provenance(self) -> Provenance:
        return Provenance(
            name=self.name,
            library_version=self._version,
            target_spec_version="0.31.2",
            is_reference=True,
            detail=f"built libcmark via ctypes ({self._lib_path}); "
            f"RAW=CMARK_OPT_UNSAFE, SAFE=default",
        )
