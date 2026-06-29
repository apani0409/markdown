"""Adapter for mistletoe's default HTML renderer.

Note: this module is ``cm_difftest.adapters.mistletoe``; ``import mistletoe``
below resolves to the top-level package (Python 3 absolute imports), not to this
module.
"""
from __future__ import annotations

import importlib.metadata as _meta

from cm_difftest.adapters.base import Adapter, Mode, Provenance

__all__ = ["MistletoeAdapter"]


class MistletoeAdapter(Adapter):
    """mistletoe with its default HTML renderer (passes the CommonMark spec).

    mistletoe has a single rendering mode and **no built-in sanitiser** — it
    passes raw HTML and dangerous URLs through unchanged. So RAW and SAFE render
    identically here; the Phase 3 security comparison records this posture
    (sanitises neither HTML nor URLs), which is itself a security note for users.
    """

    name = "mistletoe"

    def __init__(self) -> None:
        import mistletoe  # top-level package

        self._mistletoe = mistletoe

    def render(self, markdown: str, *, mode: Mode = Mode.RAW) -> str:
        # mistletoe.markdown() builds a fresh HTMLRenderer per call; it has no
        # raw/safe switch, so the same output is used for both modes.
        return self._mistletoe.markdown(markdown)

    def provenance(self) -> Provenance:
        return Provenance(
            name=self.name,
            library_version=_meta.version("mistletoe"),
            # mistletoe does not declare a specific spec version (its metadata
            # says only "follows the CommonMark specification").
            target_spec_version="not declared",
            is_reference=False,
            detail="default HTMLRenderer; no sanitiser (raw HTML + URLs pass through)",
        )
