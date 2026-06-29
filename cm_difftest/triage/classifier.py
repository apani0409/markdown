"""Triage classifier (spec §7.5).

Categorise a :class:`~cm_difftest.runner.result.Comparison` and surface the
minimal information a human needs to make the call. The classifier is
deliberately conservative: it assigns objective categories (agreement, crash,
spec non-compliance, inter-parser disagreement) and attaches *flags* for the
judgements that require a human (possible version skew, possible security
relevance) rather than deciding them itself (spec §9 keeps a human gate).

``normalization_artifact`` exists in the taxonomy but is never assigned: the
runner compares *normalized* output, so a pure formatting difference produces no
divergence at all. M1 validates this empirically (the reference matches spec.txt
on every example), i.e. the artifact rate is zero.
"""
from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field

from cm_difftest.adapters.base import Provenance
from cm_difftest.runner.result import Comparison

__all__ = ["Category", "Classification", "classify", "DANGEROUS_PATTERNS"]


class Category(enum.Enum):
    AGREEMENT = "agreement"  # not a finding
    SPEC_NONCOMPLIANCE = "spec_noncompliance"
    INTER_PARSER_DISAGREEMENT = "inter_parser_disagreement"
    CRASH = "crash"
    SECURITY_CANDIDATE = "security_candidate"
    VERSION_SKEW = "version_skew"
    NORMALIZATION_ARTIFACT = "normalization_artifact"

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value


# Executable sinks worth a closer look when one impl emits them and another
# escapes them (spec §6). Used only to *flag*, never to decide.
DANGEROUS_PATTERNS = [
    re.compile(r"<script\b", re.I),
    re.compile(r"javascript:", re.I),
    re.compile(r"vbscript:", re.I),
    re.compile(r"\bdata:text/html", re.I),
    re.compile(r"\son\w+\s*=", re.I),  # event-handler attribute
    re.compile(r"<iframe\b", re.I),
]


@dataclass
class Classification:
    category: Category
    offenders: list[str] = field(default_factory=list)  # likely-wrong impls
    agreeing: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    summary: str = ""


def _provenance_map(provenance):
    if provenance is None:
        return {}
    if isinstance(provenance, dict):
        return provenance
    return {p.name: p for p in provenance}


def _version_skew_flag(offenders, provmap, *, baseline_spec="0.31.2") -> bool:
    """Heuristic: do all offenders target a different/undeclared spec version?

    If every offender declares a spec version != the baseline (or "not declared"),
    the divergence *might* be version skew and a human must check (spec §5).
    """
    if not offenders or not provmap:
        return False
    for name in offenders:
        prov: Provenance | None = provmap.get(name)
        if prov is None:
            return False
        if prov.target_spec_version == baseline_spec:
            return False  # an offender that targets the baseline -> not skew
    return True


def _security_flag(comp: Comparison) -> bool:
    """Flag if some impl emits a dangerous sink that another does not."""
    hits = []
    for r in comp.results:
        text = r.html or ""
        present = any(p.search(text) for p in DANGEROUS_PATTERNS)
        hits.append(present)
    expected_has = None
    if comp.expected_html is not None:
        expected_has = any(p.search(comp.expected_html) for p in DANGEROUS_PATTERNS)
    # Security-relevant iff impls disagree on whether a sink is present, or an
    # impl emits one the expected output escapes.
    if len(set(hits)) > 1:
        return True
    if expected_has is False and any(hits):
        return True
    return False


def classify(comp: Comparison, provenance=None) -> Classification:
    """Classify a comparison. ``provenance`` is an iterable/dict of Provenance."""
    provmap = _provenance_map(provenance)
    names = [r.adapter for r in comp.results]

    # 1. Crash class first — a parser must never fail on untrusted input (§3).
    failures = [r for r in comp.results if not r.ok]
    if failures:
        flags = []
        if _security_flag(comp):
            flags.append("possible_security_candidate")
        offenders = [r.adapter for r in failures]
        return Classification(
            Category.CRASH,
            offenders=offenders,
            agreeing=[n for n in names if n not in offenders],
            flags=flags,
            summary="; ".join(f"{r.adapter}: {r.error}" for r in failures),
        )

    # All adapters returned OK from here.
    flags = []
    if _security_flag(comp):
        flags.append("possible_security_candidate")

    # 2. Static regime: ground truth is spec.txt's expected output.
    if comp.expected_normalized is not None:
        offenders = [
            r.adapter for r in comp.results if r.normalized != comp.expected_normalized
        ]
        if not offenders:
            return Classification(Category.AGREEMENT, agreeing=names, flags=flags,
                                  summary="all match spec.txt")
        if _version_skew_flag(offenders, provmap):
            flags.append("possible_version_skew")
        return Classification(
            Category.SPEC_NONCOMPLIANCE,
            offenders=offenders,
            agreeing=[n for n in names if n not in offenders],
            flags=flags,
            summary=f"{', '.join(offenders)} disagree with spec.txt expected output",
        )

    # 3. Dynamic regime: no expected output; cmark is the tiebreaker (§3.B).
    if not comp.has_divergence():
        return Classification(Category.AGREEMENT, agreeing=names, flags=flags,
                              summary="all implementations agree")

    offenders = comp.reference_disagreements()
    if not offenders:
        # No (OK) reference, or reference is itself the minority. Fall back to
        # the smallest disagreeing group(s) as offenders.
        groups = comp.agreement_groups()
        groups_sorted = sorted(groups, key=len)
        offenders = [n for g in groups_sorted[:-1] for n in g] if len(groups) > 1 else []
    if _version_skew_flag(offenders, provmap):
        flags.append("possible_version_skew")
    return Classification(
        Category.INTER_PARSER_DISAGREEMENT,
        offenders=offenders,
        agreeing=[n for n in names if n not in offenders],
        flags=flags,
        summary=f"implementations disagree; likely-wrong (vs cmark): "
        f"{', '.join(offenders) if offenders else 'undetermined'}",
    )
