"""Findings log for the dynamic / fuzzed regime (spec §7.8).

Each finding records everything needed to reproduce and triage a divergence:
the exact input, every implementation's output, the classification, the
spec-version provenance, and a runnable reproducer. Findings are written to the
git-ignored ``findings/`` directory and treated as private until any
security-relevant ones are responsibly disclosed (spec §6).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from cm_difftest.runner.result import Comparison
from cm_difftest.triage import Classification

__all__ = ["Finding", "make_finding", "write_json", "write_markdown", "reproducer_for"]


@dataclass
class Finding:
    id: str
    input_markdown: str
    input_repr: str
    mode: str
    category: str
    offenders: list[str]
    flags: list[str]
    outputs: dict[str, dict]
    expected_html: str | None
    reference: str | None
    provenance: list[dict]
    reproducer: str
    summary: str = ""
    status: str = "open"  # open | triaging | filed | disclosed | rejected | duplicate
    notes: str = ""
    extra: dict = field(default_factory=dict)


def reproducer_for(markdown: str, mode: str) -> str:
    """A minimal, runnable snippet that re-renders the input across adapters."""
    return (
        "from cm_difftest.adapters import default_adapters, Mode\n"
        f"md = {markdown!r}\n"
        f"for a in default_adapters():\n"
        f"    print(a.name, repr(a.render(md, mode=Mode.{mode.upper()})))\n"
    )


def make_finding(
    finding_id: str,
    comp: Comparison,
    classification: Classification,
    *,
    provenance=None,
    status: str = "open",
    notes: str = "",
) -> Finding:
    provlist = []
    if provenance is not None:
        for p in provenance:
            provlist.append(
                {
                    "name": p.name,
                    "library_version": p.library_version,
                    "target_spec_version": p.target_spec_version,
                    "is_reference": p.is_reference,
                    "detail": p.detail,
                }
            )
    outputs = {
        r.adapter: {
            "status": r.status.value,
            "html": r.html,
            "normalized": r.normalized,
            "error": r.error,
        }
        for r in comp.results
    }
    return Finding(
        id=finding_id,
        input_markdown=comp.markdown,
        input_repr=repr(comp.markdown),
        mode=comp.mode,
        category=classification.category.value,
        offenders=classification.offenders,
        flags=classification.flags,
        outputs=outputs,
        expected_html=comp.expected_html,
        reference=comp.reference,
        provenance=provlist,
        reproducer=reproducer_for(comp.markdown, comp.mode),
        summary=classification.summary,
        status=status,
        notes=notes,
    )


def write_json(findings: list[Finding], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([asdict(f) for f in findings], fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def write_markdown(findings: list[Finding], path: str) -> None:
    lines: list[str] = []
    a = lines.append
    a(f"# Findings log ({len(findings)})")
    a("")
    for f in findings:
        a(f"## {f.id} — {f.category}")
        a("")
        a(f"- **status:** {f.status}")
        a(f"- **mode:** {f.mode}")
        a(f"- **offenders (likely-wrong):** {', '.join(f.offenders) or 'undetermined'}")
        if f.flags:
            a(f"- **flags:** {', '.join(f.flags)}")
        a(f"- **summary:** {f.summary}")
        a("")
        a(f"Input (repr): `{f.input_repr}`")
        a("")
        a("| Parser | Status | Output |")
        a("|---|---|---|")
        for name, out in f.outputs.items():
            html = out["html"] if out["html"] is not None else out["error"]
            cell = (html or "").replace("|", "\\|").replace("\n", "↵")
            if len(cell) > 200:
                cell = cell[:197] + "..."
            a(f"| {name} | {out['status']} | `{cell}` |")
        a("")
        if f.expected_html is not None:
            a(f"Expected: `{f.expected_html.replace(chr(10), '↵')}`")
            a("")
        a("Reproducer:")
        a("")
        a("```python")
        a(f.reproducer.rstrip())
        a("```")
        a("")
        if f.notes:
            a(f"Notes: {f.notes}")
            a("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
