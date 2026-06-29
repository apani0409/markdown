"""Command-line interface for cm-difftest.

    cm-difftest scorecard [--out DIR] [--date YYYY-MM-DD]
    cm-difftest provenance
    cm-difftest render "<markdown>" [--mode raw|safe]

The ``scorecard`` command is the M1 deliverable: it runs the full spec.txt
corpus across all SUTs + the cmark reference and writes a JSON + Markdown
compliance scorecard, printing the M1 done-criterion (normalizer false-positive
rate).
"""
from __future__ import annotations

import argparse
import os
import sys

from cm_difftest import SPEC_VERSION
from cm_difftest.adapters import Mode, default_adapters
from cm_difftest.corpus import load_spec
from cm_difftest.report import scorecard as sc
from cm_difftest.runner import DifferentialRunner


def _cmd_scorecard(args: argparse.Namespace) -> int:
    examples = load_spec()
    runner = DifferentialRunner(timeout_s=args.timeout)
    print(f"Running {len(examples)} spec.txt examples (spec {SPEC_VERSION}) "
          f"across {len(runner.adapters)} implementations...", file=sys.stderr)
    card = sc.build_scorecard(examples, runner, generated=args.date)

    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "scorecard.json")
    md_path = os.path.join(args.out, "scorecard.md")
    sc.write_json(card, json_path)
    sc.write_markdown(card, md_path)

    totals = card.totals()
    ref_pass, ref_total = card.reference_fidelity()
    print()
    print(f"Compliance scorecard (CommonMark {card.spec_version}, {card.total} examples)")
    print("-" * 60)
    for name in card.parser_names():
        role = " (reference)" if name == card.reference_name else ""
        pct = 100 * totals[name] / card.total if card.total else 0
        print(f"  {name:18} {totals[name]:>4}/{card.total}  {pct:5.1f}%{role}")
    print("-" * 60)
    print(f"M1 criterion — reference fidelity: {ref_pass}/{ref_total} "
          f"(normalizer false positives: {ref_total - ref_pass})")
    print(f"               normalization artifacts: {card.normalization_artifacts()}")
    print()
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")

    # Exit non-zero if the M1 done-criterion is not met.
    ok = (ref_pass == ref_total) and (card.normalization_artifacts() == 0)
    if not ok:
        print("M1 CRITERION NOT MET: normalization is producing false positives.",
              file=sys.stderr)
        return 1
    return 0


def _cmd_provenance(args: argparse.Namespace) -> int:
    for a in default_adapters():
        p = a.provenance()
        role = "reference" if p.is_reference else "SUT"
        print(f"{p.name:18} lib={p.library_version:10} "
              f"target-spec={p.target_spec_version:13} [{role}] {p.detail}")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    mode = Mode.SAFE if args.mode == "safe" else Mode.RAW
    runner = DifferentialRunner(mode=mode, timeout_s=args.timeout)
    comp = runner.run(args.markdown)
    for r in comp.results:
        if r.ok:
            print(f"{r.adapter:18} {r.html!r}")
        else:
            print(f"{r.adapter:18} [{r.status}] {r.error}")
    if comp.has_divergence():
        print(f"\nDIVERGENCE. likely-wrong vs cmark: "
              f"{', '.join(comp.reference_disagreements()) or 'undetermined'}")
    else:
        print("\nAll implementations agree.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cm-difftest", description=__doc__)
    parser.add_argument("--timeout", type=float, default=5.0,
                        help="per-input timeout in seconds (default 5)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_score = sub.add_parser("scorecard", help="run the spec.txt compliance scorecard")
    p_score.add_argument("--out", default="reports", help="output directory (default reports/)")
    p_score.add_argument("--date", default=None, help="value for the report's 'generated' field")
    p_score.set_defaults(func=_cmd_scorecard)

    p_prov = sub.add_parser("provenance", help="print parser/version provenance")
    p_prov.set_defaults(func=_cmd_provenance)

    p_render = sub.add_parser("render", help="render one input across all parsers")
    p_render.add_argument("markdown", help="markdown input")
    p_render.add_argument("--mode", choices=["raw", "safe"], default="raw")
    p_render.set_defaults(func=_cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
