"""Adapter for marko's default Markdown renderer.

Note: this module is ``cm_difftest.adapters.marko``; ``import marko`` below
resolves to the top-level package (Python 3 absolute imports), not to this
module.
"""
from __future__ import annotations

import importlib.metadata as _meta

from cm_difftest.adapters.base import Adapter, Mode, ModeNotSupported, Provenance

__all__ = ["MarkoAdapter"]


class MarkoAdapter(Adapter):
    """marko's default ``Markdown()`` (explicitly targets CommonMark 0.31.2).

    marko passes raw HTML through by default (RAW). It ships no built-in
    sanitiser, so SAFE is deferred to Phase 3.
    """

    name = "marko"

    def __init__(self) -> None:
        import marko  # top-level package

        self._md = marko.Markdown()

    def render(self, markdown: str, *, mode: Mode = Mode.RAW) -> str:
        if mode is Mode.RAW:
            return self._md(markdown)
        raise ModeNotSupported(
            "marko has no built-in safe mode; SAFE comparison is Phase 3"
        )

    def provenance(self) -> Provenance:
        return Provenance(
            name=self.name,
            library_version=_meta.version("marko"),
            target_spec_version="0.31.2",
            is_reference=False,
            detail="default Markdown(); targets CommonMark 0.31.2",
        )
