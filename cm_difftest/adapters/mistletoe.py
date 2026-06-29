"""Adapter for mistletoe's default HTML renderer.

Note: this module is ``cm_difftest.adapters.mistletoe``; ``import mistletoe``
below resolves to the top-level package (Python 3 absolute imports), not to this
module.
"""
from __future__ import annotations

import importlib.metadata as _meta

from cm_difftest.adapters.base import Adapter, Mode, ModeNotSupported, Provenance

__all__ = ["MistletoeAdapter"]


class MistletoeAdapter(Adapter):
    """mistletoe with its default HTML renderer (passes the CommonMark spec).

    mistletoe passes raw HTML through by default (RAW). It ships no built-in
    sanitiser, so SAFE is deferred to Phase 3 (raising :class:`ModeNotSupported`
    rather than silently comparing a non-equivalent mode).
    """

    name = "mistletoe"

    def __init__(self) -> None:
        import mistletoe  # top-level package

        self._mistletoe = mistletoe

    def render(self, markdown: str, *, mode: Mode = Mode.RAW) -> str:
        if mode is Mode.RAW:
            # mistletoe.markdown() builds a fresh HTMLRenderer per call.
            return self._mistletoe.markdown(markdown)
        raise ModeNotSupported(
            "mistletoe has no built-in safe mode; SAFE comparison is Phase 3"
        )

    def provenance(self) -> Provenance:
        return Provenance(
            name=self.name,
            library_version=_meta.version("mistletoe"),
            # mistletoe does not declare a specific spec version (its metadata
            # says only "follows the CommonMark specification").
            target_spec_version="not declared",
            is_reference=False,
            detail="default HTMLRenderer; spec version not pinned by project",
        )
