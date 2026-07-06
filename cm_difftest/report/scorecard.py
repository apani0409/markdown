"""Compliance scorecard for the static corpus regime (spec §7.8, M1 deliverable).

Runs every example through the differential runner, records per-parser pass/fail
against spec.txt's expected output, and writes the result as JSON + a
human-readable Markdown table. Also records the M1 done-criterion metric: the
reference's fidelity to spec.txt (the normalizer false-positive rate).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from cm_difftest.adapters.base import Provenance
from cm_difftest.corpus import Example
from cm_difftest.runner import DifferentialRunner
from cm_difftest.runner.result import Status
from cm_difftest.triage import Category, classify

__all__ = [
    "ExampleOutcome",
    "Scorecard",
    "build_scorecard",
    "write_json",
    "write_markdown",
]


@dataclass
class ExampleOutcome:
    number: int
    section: str
    markdown: str
    expected_html: str
    passed: dict[str, bool]  # parser name -> matched expected
    status: dict[str, str]  # parser name -> Status value
    error: dict[str, str]  # parser name -> error (only failures)
    category: str
    offenders: list[str]
    flags: list[str]


@dataclass
class Scorecard:
    spec_version: str
    provenance: list[dict]  # serialized Provenance
    sut_names: list[str]
    reference_name: str | None
    outcomes: list[ExampleOutcome]
    generated: str | None = None
    metadata: dict = field(default_factory=dict)

    # --- summaries -------------------------------------------------------- #
    @property
    def total(self) -> int:
        return len(self.outcomes)

    def parser_names(self) -> list[str]:
        return self.sut_names + ([self.reference_name] if self.reference_name else [])

    def totals(self) -> dict[str, int]:
        """parser -> number of examples passed."""
        counts = {name: 0 for name in self.parser_names()}
        for o in self.outcomes:
            for name, ok in o.passed.items():
                if ok:
                    counts[name] += 1
        return counts

    def by_section(self) -> dict[str, dict[str, tuple[int, int]]]:
        """section -> parser -> (passed, total)."""
        out: dict[str, dict[str, list[int]]] = {}
        for o in self.outcomes:
            sec = out.setdefault(o.section, {n: [0, 0] for n in self.parser_names()})
            for name in self.parser_names():
                sec[name][1] += 1
                if o.passed.get(name):
                    sec[name][0] += 1
        return {s: {n: (v[0], v[1]) for n, v in d.items()} for s, d in out.items()}

    def failures_for(self, name: str) -> list[ExampleOutcome]:
        return [o for o in self.outcomes if not o.passed.get(name, False)]

    def reference_fidelity(self) -> tuple[int, int]:
        """(reference passes, total) — the M1 normalizer false-positive metric."""
        if not self.reference_name:
            return (0, self.total)
        return (self.totals().get(self.reference_name, 0), self.total)

    def normalization_artifacts(self) -> int:
        return sum(1 for o in self.outcomes if o.category == Category.NORMALIZATION_ARTIFACT.value)


def build_scorecard(
    examples: list[Example],
    runner: DifferentialRunner | None = None,
    *,
    generated: str | None = None,
) -> Scorecard:
    runner = runner or DifferentialRunner()
    provenance: list[Provenance] = runner.provenance()
    sut_names = [p.name for p in provenance if not p.is_reference]
    reference_name = next((p.name for p in provenance if p.is_reference), None)

    outcomes: list[ExampleOutcome] = []
    for ex in examples:
        comp = runner.run(ex.markdown, expected_html=ex.html)
        cls = classify(comp, provenance)
        passed, status, error = {}, {}, {}
        for r in comp.results:
            status[r.adapter] = r.status.value
            matched = comp.matches_expected(r.adapter)
            passed[r.adapter] = bool(matched)
            if r.status is not Status.OK:
                error[r.adapter] = r.error or ""
        outcomes.append(
            ExampleOutcome(
                number=ex.number,
                section=ex.section,
                markdown=ex.markdown,
                expected_html=ex.html,
                passed=passed,
                status=status,
                error=error,
                category=cls.category.value,
                offenders=cls.offenders,
                flags=cls.flags,
            )
        )

    return Scorecard(
        spec_version=_spec_version(),
        provenance=[_prov_dict(p) for p in provenance],
        sut_names=sut_names,
        reference_name=reference_name,
        outcomes=outcomes,
        generated=generated,
    )


def _spec_version() -> str:
    from cm_difftest import SPEC_VERSION

    return SPEC_VERSION


def _prov_dict(p: Provenance) -> dict:
    return {
        "name": p.name,
        "library_version": p.library_version,
        "target_spec_version": p.target_spec_version,
        "is_reference": p.is_reference,
        "detail": p.detail,
    }


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #
def to_dict(card: Scorecard) -> dict:
    totals = card.totals()
    return {
        "spec_version": card.spec_version,
        "generated": card.generated,
        "provenance": card.provenance,
        "sut_names": card.sut_names,
        "reference_name": card.reference_name,
        "summary": {
            "total_examples": card.total,
            "totals": totals,
            "pass_rate": {
                n: round(100 * c / card.total, 2) if card.total else 0.0
                for n, c in totals.items()
            },
            "reference_fidelity": card.reference_fidelity(),
            "normalization_artifacts": card.normalization_artifacts(),
        },
        "by_section": {
            sec: {n: list(v) for n, v in d.items()}
            for sec, d in card.by_section().items()
        },
        "outcomes": [asdict(o) for o in card.outcomes],
    }


def write_json(card: Scorecard, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(to_dict(card), fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _pct(passed: int, total: int) -> str:
    return f"{100 * passed / total:.1f}%" if total else "n/a"


def write_markdown(card: Scorecard, path: str) -> None:
    names = card.parser_names()
    totals = card.totals()
    lines: list[str] = []
    a = lines.append

    a(f"# CommonMark compliance scorecard — spec {card.spec_version}")
    a("")
    if card.generated:
        a(f"_Generated: {card.generated}_")
        a("")
    a(
        "Per-parser pass/fail against the official CommonMark `spec.txt` "
        f"({card.total} examples), compared after the official `normalize_html`."
    )
    a("")

    # Provenance
    a("## Provenance")
    a("")
    a("| Parser | Library version | Target spec | Role |")
    a("|---|---|---|---|")
    for p in card.provenance:
        role = "reference (oracle)" if p["is_reference"] else "SUT"
        a(f"| {p['name']} | {p['library_version']} | {p['target_spec_version']} | {role} |")
    a("")

    # Overall
    a("## Overall")
    a("")
    a("| Parser | Passed | Total | Pass rate |")
    a("|---|---:|---:|---:|")
    for n in names:
        a(f"| {n} | {totals[n]} | {card.total} | {_pct(totals[n], card.total)} |")
    a("")

    # M1 criterion
    ref_pass, ref_total = card.reference_fidelity()
    fp = ref_total - ref_pass
    a("## M1 done-criterion (normalization false positives)")
    a("")
    a(
        f"- Reference (`{card.reference_name}`) matches spec.txt on "
        f"**{ref_pass}/{ref_total}** examples."
    )
    a(
        f"- Normalizer false-positive rate: **{_pct(fp, ref_total) if fp else '0.0%'}** "
        f"({fp} example(s))."
    )
    a(f"- Comparisons classified as normalization artifacts: **{card.normalization_artifacts()}**.")
    a("")

    # Per-section
    a("## By section")
    a("")
    header = "| Section | " + " | ".join(names) + " |"
    sep = "|---|" + "|".join(["---:"] * len(names)) + "|"
    a(header)
    a(sep)
    by_sec = card.by_section()
    for sec in by_sec:
        cells = []
        for n in names:
            p, t = by_sec[sec][n]
            cells.append(f"{p}/{t}")
        a(f"| {sec} | " + " | ".join(cells) + " |")
    a("")

    # Failing examples per SUT
    a("## Failing examples (SUTs)")
    a("")
    for n in card.sut_names:
        fails = card.failures_for(n)
        a(f"### {n} — {len(fails)} failing")
        a("")
        if not fails:
            a("_None — fully compliant._")
            a("")
            continue
        a("| # | Section | Category | Flags |")
        a("|---:|---|---|---|")
        for o in fails:
            flags = ", ".join(o.flags) if o.flags else ""
            a(f"| {o.number} | {o.section} | {o.category} | {flags} |")
        a("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
