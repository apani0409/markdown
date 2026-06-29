"""Result structures for the differential runner (spec §7.4).

A :class:`RenderResult` captures one adapter's outcome on one input (output or a
documented failure — never an uncaught crash). A :class:`Comparison` collects the
results for all adapters on a single input and exposes the agreement matrix used
by triage.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field

__all__ = ["Status", "RenderResult", "Comparison"]


class Status(enum.Enum):
    """Outcome class for a single guarded render."""

    OK = "ok"
    EXCEPTION = "exception"  # adapter raised (incl. RecursionError)
    TIMEOUT = "timeout"  # exceeded the per-input time limit
    MEMORY = "memory"  # MemoryError / RLIMIT_AS hit
    CRASH = "crash"  # process died (segfault/abort) under isolation

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value


@dataclass(frozen=True)
class RenderResult:
    """One adapter's outcome on one input."""

    adapter: str
    status: Status
    html: str | None = None
    normalized: str | None = None
    error: str | None = None  # "ExceptionType: message" when not OK
    error_type: str | None = None
    duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status is Status.OK

    def outcome_key(self) -> tuple:
        """A hashable key that is equal iff two results "agree".

        OK results agree iff their normalized HTML matches. Failures agree iff
        they share the same status and exception type (so two parsers failing
        the same way are one group, but a success and a failure never agree).
        """
        if self.ok:
            return ("ok", self.normalized)
        return ("err", self.status.value, self.error_type)


@dataclass
class Comparison:
    """All adapters' results on one input, plus agreement analysis.

    ``results`` preserves adapter order. ``expected_*`` is set only in the static
    corpus regime (where spec.txt provides ground truth).
    """

    markdown: str
    mode: str
    results: list[RenderResult]
    expected_html: str | None = None
    expected_normalized: str | None = None
    reference: str | None = None  # name of the reference adapter (cmark), if present
    metadata: dict = field(default_factory=dict)

    def by_name(self, name: str) -> RenderResult | None:
        for r in self.results:
            if r.adapter == name:
                return r
        return None

    def agreement_groups(self) -> list[list[str]]:
        """Adapter names grouped by :meth:`RenderResult.outcome_key`.

        Groups are ordered by first appearance; names within a group keep input
        order. A single group means unanimous agreement.
        """
        groups: dict[tuple, list[str]] = {}
        for r in self.results:
            groups.setdefault(r.outcome_key(), []).append(r.adapter)
        return list(groups.values())

    def has_divergence(self) -> bool:
        """True iff the adapters do not all agree (different output or failure)."""
        return len({r.outcome_key() for r in self.results}) > 1

    def has_failure(self) -> bool:
        """True iff any adapter did not return OK (crash class, spec §3)."""
        return any(not r.ok for r in self.results)

    def reference_disagreements(self) -> list[str]:
        """OK adapters whose normalized output differs from the reference.

        The reference (cmark) is the tiebreaker (spec §3.B): these are the
        likely-buggy implementations. Empty if there is no OK reference.
        """
        if self.reference is None:
            return []
        ref = self.by_name(self.reference)
        if ref is None or not ref.ok:
            return []
        return [
            r.adapter
            for r in self.results
            if r.adapter != self.reference and r.ok and r.normalized != ref.normalized
        ]

    def matches_expected(self, name: str) -> bool | None:
        """Static regime: does adapter *name* match spec.txt's expected HTML?

        Returns None if there is no expected output or the adapter failed.
        """
        if self.expected_normalized is None:
            return None
        r = self.by_name(name)
        if r is None or not r.ok:
            return None
        return r.normalized == self.expected_normalized
