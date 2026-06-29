"""Adapter for markdown-it-py in CommonMark mode."""
from __future__ import annotations

import importlib.metadata as _meta

from cm_difftest.adapters.base import Adapter, Mode, Provenance

__all__ = ["MarkdownItAdapter"]


class MarkdownItAdapter(Adapter):
    """``MarkdownIt("commonmark")`` (advertises 100% CommonMark support).

    The ``commonmark`` preset enables ``html=True`` (raw HTML passthrough), which
    is our RAW mode. SAFE mode disables raw HTML (``html=False``); markdown-it
    additionally validates link URLs by default, rejecting ``javascript:`` etc.
    in both modes (a real behavioural difference vs cmark, surfaced as a finding,
    not hidden here).
    """

    name = "markdown-it-py"

    def __init__(self) -> None:
        from markdown_it import MarkdownIt

        self._raw = MarkdownIt("commonmark")
        self._safe = MarkdownIt("commonmark", {"html": False})

    def render(self, markdown: str, *, mode: Mode = Mode.RAW) -> str:
        if mode is Mode.RAW:
            return self._raw.render(markdown)
        return self._safe.render(markdown)

    def provenance(self) -> Provenance:
        return Provenance(
            name=self.name,
            library_version=_meta.version("markdown-it-py"),
            target_spec_version="0.31.2",
            is_reference=False,
            detail="MarkdownIt('commonmark'); RAW=html:true, SAFE=html:false",
        )
