"""Uniform parser-adapter interface (spec §7.1).

Every implementation under test (and the cmark reference) is wrapped so the rest
of the harness sees a single shape::

    adapter.render(markdown, mode=Mode.RAW) -> html
    adapter.provenance() -> Provenance(name, library_version, target_spec, ...)

All parser-specific API quirks are isolated here. Provenance is recorded in
every report so divergences are interpretable (spec §5).
"""
from __future__ import annotations

import abc
import enum
from dataclasses import dataclass

__all__ = [
    "Mode",
    "Provenance",
    "Adapter",
    "AdapterError",
    "ModeNotSupported",
]


class Mode(enum.Enum):
    """HTML/URL safety mode for a comparison (spec §6).

    Never mix modes within a single comparison.
    """

    #: Raw HTML passed through, URLs not sanitized. Matches spec.txt's expected
    #: output and is the default for compliance (M1) and differential fuzzing
    #: (M2). For cmark this is ``CMARK_OPT_UNSAFE``.
    RAW = "raw"

    #: Raw HTML escaped/stripped and dangerous URL schemes neutralised. Used for
    #: the Phase 3 security comparison only.
    SAFE = "safe"


class AdapterError(RuntimeError):
    """Raised when an adapter cannot be constructed (e.g. missing reference lib)."""


class ModeNotSupported(NotImplementedError):
    """Raised when a parser has no faithful implementation of the requested mode.

    M1/M2 only exercise :attr:`Mode.RAW`; some SAFE modes are deferred to Phase 3.
    """


@dataclass(frozen=True)
class Provenance:
    """Identity recorded for every parser in every report (spec §5)."""

    name: str
    library_version: str
    target_spec_version: str
    is_reference: bool = False
    detail: str = ""


class Adapter(abc.ABC):
    """Base class for a single parser wrapper."""

    #: Stable short identifier used as a column key in reports.
    name: str = "adapter"
    #: Whether this adapter is the ground-truth oracle (cmark).
    is_reference: bool = False

    @abc.abstractmethod
    def render(self, markdown: str, *, mode: Mode = Mode.RAW) -> str:
        """Render *markdown* to HTML in the given *mode*.

        Raises :class:`ModeNotSupported` if the mode has no faithful mapping.
        Must not silently fall back to a different mode.
        """

    @abc.abstractmethod
    def provenance(self) -> Provenance:
        """Return identity/version provenance for reports."""

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<Adapter {self.name}>"
