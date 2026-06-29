"""Adapters subpackage: uniform parser wrappers + cmark reference (spec §7.1).

Public surface:

    Mode, Provenance, Adapter, AdapterError, ModeNotSupported   (interface)
    default_adapters()   -> [3 SUTs + cmark reference]
    sut_adapters()       -> [3 SUTs]
    reference_adapter()  -> cmark
    get_adapter(name)    -> a single adapter by name
"""
from __future__ import annotations

from cm_difftest.adapters.base import (
    Adapter,
    AdapterError,
    Mode,
    ModeNotSupported,
    Provenance,
)
from cm_difftest.adapters.cmark import CmarkAdapter
from cm_difftest.adapters.markdownit import MarkdownItAdapter
from cm_difftest.adapters.marko import MarkoAdapter
from cm_difftest.adapters.mistletoe import MistletoeAdapter

__all__ = [
    "Mode",
    "Provenance",
    "Adapter",
    "AdapterError",
    "ModeNotSupported",
    "MarkdownItAdapter",
    "MistletoeAdapter",
    "MarkoAdapter",
    "CmarkAdapter",
    "default_adapters",
    "sut_adapters",
    "reference_adapter",
    "get_adapter",
    "ADAPTER_CLASSES",
]

# Construction order is the stable column order used across all reports: the
# three SUTs first, the reference last.
ADAPTER_CLASSES = {
    "markdown-it-py": MarkdownItAdapter,
    "mistletoe": MistletoeAdapter,
    "marko": MarkoAdapter,
    "cmark": CmarkAdapter,
}


def sut_adapters() -> list[Adapter]:
    """The three systems under test (no reference)."""
    return [MarkdownItAdapter(), MistletoeAdapter(), MarkoAdapter()]


def reference_adapter() -> Adapter:
    """The cmark ground-truth oracle."""
    return CmarkAdapter()


def default_adapters() -> list[Adapter]:
    """All adapters in stable order: the three SUTs followed by cmark."""
    return [*sut_adapters(), reference_adapter()]


def get_adapter(name: str) -> Adapter:
    try:
        return ADAPTER_CLASSES[name]()
    except KeyError as exc:
        raise AdapterError(
            f"unknown adapter {name!r}; known: {sorted(ADAPTER_CLASSES)}"
        ) from exc
