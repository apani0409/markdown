"""Adapter for marko's default Markdown renderer.

Note: this module is ``cm_difftest.adapters.marko``; ``import marko`` below
resolves to the top-level package (Python 3 absolute imports), not to this
module.
"""
from __future__ import annotations

import importlib.metadata as _meta

from cm_difftest.adapters.base import Adapter, Mode, Provenance

__all__ = ["MarkoAdapter"]


class MarkoAdapter(Adapter):
    """marko's default ``Markdown()`` (explicitly targets CommonMark 0.31.2).

    marko has a single rendering mode. Its safety posture (spec §6): it rewrites
    dangerous URL schemes (e.g. ``javascript:``) to ``#harmful-link`` but passes
    raw HTML through. So RAW and SAFE render identically here; the Phase 3
    security comparison records this posture (URL-sanitising, not HTML-sanitising)
    rather than relying on a separate flag.
    """

    name = "marko"

    def __init__(self) -> None:
        import marko  # top-level package

        self._md = marko.Markdown()

    def render(self, markdown: str, *, mode: Mode = Mode.RAW) -> str:
        # marko exposes no raw/safe switch; its one mode is used for both.
        return self._md(markdown)

    def provenance(self) -> Provenance:
        return Provenance(
            name=self.name,
            library_version=_meta.version("marko"),
            target_spec_version="0.31.2",
            is_reference=False,
            detail="default Markdown(); URL-sanitising (#harmful-link), raw HTML passes through",
        )
