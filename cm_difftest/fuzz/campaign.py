"""Differential fuzzing campaign (spec §8, §9).

Ties the pieces together: generate structure-aware inputs, run them through the
differential runner, keep genuine divergences, deduplicate by a structural
signature, minimize each representative, and emit findings. Crashes (should they
ever occur) are always kept. Determinism is preserved via the generator seed and
by recording the exact input bytes of every finding.

This module separates *signal* from *noise* but does not make the final
human-only calls (version-skew vs genuine bug, security disclosure): it surfaces
flags and the cmark tiebreaker so a human can triage (spec §9).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from cm_difftest.fuzz.generator import StructureAwareGenerator, corpus_seeds
from cm_difftest.report.findings import Finding, make_finding
from cm_difftest.runner import DifferentialRunner
from cm_difftest.triage import Category, classify
from cm_difftest.triage.minimizer import minimize, same_divergence_predicate

__all__ = ["CampaignConfig", "CampaignResult", "run_campaign"]

_TAG_RE = re.compile(r"<\s*/?\s*([a-zA-Z][a-zA-Z0-9]*)")


def _tag_multiset(html: str | None) -> frozenset:
    if not html:
        return frozenset()
    return frozenset((t.lower(), html.lower().count("<" + t.lower())) for t in _TAG_RE.findall(html))


def _signature(comp, cls) -> tuple:
    """A structural signature grouping "the same kind of" divergence.

    (category, sorted offenders, symmetric tag difference vs the reference).
    """
    ref = comp.by_name(comp.reference) if comp.reference else None
    ref_tags = _tag_multiset(ref.html) if ref and ref.ok else frozenset()
    diff = frozenset()
    for name in cls.offenders:
        r = comp.by_name(name)
        if r is not None and r.ok:
            diff |= _tag_multiset(r.html) ^ ref_tags
    return (cls.category.value, tuple(sorted(cls.offenders)), diff)


@dataclass
class CampaignConfig:
    iterations: int = 5000
    seed: int = 0
    max_mutations: int = 4
    timeout_s: float = 5.0
    max_findings: int = 50
    minimize_findings: bool = True
    minimize_max_calls: int = 1500
    # If True, drop divergences flagged as possible version skew (focus on the
    # parsers that target the baseline spec). Crashes are never dropped.
    drop_version_skew: bool = False
    # If set, keep only findings whose offenders intersect these names (e.g. the
    # parsers that target 0.31.2, for rock-solid bug candidates).
    require_offenders: frozenset[str] | None = None


@dataclass
class CampaignResult:
    findings: list[Finding]
    iterations: int
    divergences_seen: int
    crashes_seen: int
    unique_signatures: int
    seed: int
    provenance: list = field(default_factory=list)


def run_campaign(
    config: CampaignConfig | None = None,
    *,
    seeds: list[str] | None = None,
    runner: DifferentialRunner | None = None,
) -> CampaignResult:
    config = config or CampaignConfig()
    seeds = seeds if seeds is not None else corpus_seeds()
    runner = runner or DifferentialRunner(timeout_s=config.timeout_s)
    prov = runner.provenance()
    gen = StructureAwareGenerator(seeds, seed=config.seed, max_mutations=config.max_mutations)

    seen: set[tuple] = set()
    findings: list[Finding] = []
    divergences = 0
    crashes = 0

    for i in range(config.iterations):
        md = gen.generate_one()
        comp = runner.run(md)
        cls = classify(comp, prov)
        if cls.category is Category.AGREEMENT:
            continue
        divergences += 1
        is_crash = comp.has_failure()
        if is_crash:
            crashes += 1

        if not is_crash:
            if config.drop_version_skew and "possible_version_skew" in cls.flags:
                continue
            if config.require_offenders is not None and not (
                set(cls.offenders) & config.require_offenders
            ):
                continue

        sig = _signature(comp, cls)
        if sig in seen:
            continue
        seen.add(sig)

        if config.minimize_findings and not is_crash:
            pred = same_divergence_predicate(
                runner,
                provenance=prov,
                category=cls.category.value,
                offenders=frozenset(cls.offenders),
            )
            mini = minimize(md, pred, max_calls=config.minimize_max_calls)
            comp = runner.run(str(mini))
            cls = classify(comp, prov)
            if cls.category is Category.AGREEMENT:
                continue  # minimization drifted; skip

        finding = make_finding(
            f"F-{config.seed}-{len(findings) + 1:03d}", comp, cls, provenance=prov
        )
        findings.append(finding)
        if len(findings) >= config.max_findings:
            break

    return CampaignResult(
        findings=findings,
        iterations=i + 1,
        divergences_seen=divergences,
        crashes_seen=crashes,
        unique_signatures=len(seen),
        seed=config.seed,
        provenance=prov,
    )
