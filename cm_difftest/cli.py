"""Command-line interface for cm-difftest.

    cm-difftest scorecard [--out DIR] [--date YYYY-MM-DD]
    cm-difftest provenance
    cm-difftest render "<markdown>" [--mode raw|safe]
    cm-difftest fuzz [--iterations N] [--seed S] [--out DIR] [...]
    cm-difftest security [--iterations N] [--seed S]
    cm-difftest perf [--budget S]

The ``scorecard`` command is the M1 deliverable: it runs the full spec.txt
corpus across all SUTs + the cmark reference and writes a JSON + Markdown
compliance scorecard, printing the M1 done-criterion (normalizer false-positive
rate). The ``fuzz`` command is the M2 differential fuzzing campaign.
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


def _cmd_fuzz(args: argparse.Namespace) -> int:
    from cm_difftest.fuzz import CampaignConfig, run_campaign
    from cm_difftest.report import findings as fnd

    require = None
    if args.require_offenders:
        require = frozenset(args.require_offenders.split(","))
    config = CampaignConfig(
        iterations=args.iterations,
        seed=args.seed,
        timeout_s=args.timeout,
        max_findings=args.max_findings,
        minimize_findings=not args.no_minimize,
        drop_version_skew=args.drop_version_skew,
        require_offenders=require,
    )
    print(f"Fuzzing: {args.iterations} iterations, seed {args.seed}...", file=sys.stderr)
    result = run_campaign(config)
    print(
        f"ran={result.iterations} divergences={result.divergences_seen} "
        f"crashes={result.crashes_seen} unique={result.unique_signatures} "
        f"findings={len(result.findings)}"
    )
    # Findings go to the git-ignored findings/ dir (private until disclosed, §6).
    os.makedirs(args.out, exist_ok=True)
    jpath = os.path.join(args.out, f"findings-seed{args.seed}.json")
    mpath = os.path.join(args.out, f"findings-seed{args.seed}.md")
    fnd.write_json(result.findings, jpath)
    fnd.write_markdown(result.findings, mpath)
    print(f"Wrote {jpath}")
    print(f"Wrote {mpath}")
    for f in result.findings[:10]:
        print(f"  {f.id} [{f.category}] offenders={','.join(f.offenders) or '?'} "
              f"flags={','.join(f.flags) or '-'}  input={f.input_repr}")
    return 0


def _cmd_security(args: argparse.Namespace) -> int:
    from cm_difftest.security import scan_campaign

    print(f"Security scan: {args.iterations} vectors, seed {args.seed}...", file=sys.stderr)
    res = scan_campaign(iterations=args.iterations, seed=args.seed)
    print(f"scanned={res['scanned']}")
    print("safe-mode sink emissions (posture; not necessarily a bug):")
    for name, n in res["leak_counts"].items():
        print(f"  {name:18} {n}")
    print(f"GENUINE sanitizer bypasses: {len(res['bypasses'])}")
    for b in res["bypasses"][:20]:
        print(f"  {b['input_repr']}  {b['bypasses']}")
    if res["bypasses"]:
        # Bypasses are potential vulnerabilities: write them to git-ignored
        # findings/ (private until responsibly disclosed, spec §6).
        import json
        os.makedirs("findings", exist_ok=True)
        path = os.path.join("findings", f"security-bypasses-seed{args.seed}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res["bypasses"], fh, indent=2, ensure_ascii=False)
        print(f"\nWrote PRIVATE findings to {path} (do not publish until disclosed).")
    return 0


def _cmd_perf(args: argparse.Namespace) -> int:
    from cm_difftest.perf import run_perf

    print("Measuring algorithmic-complexity scaling per parser...", file=sys.stderr)
    results = run_perf(budget=args.budget)
    print(f"{'family':22}{'parser':16}{'exponent':>9}  status")
    for o in results:
        exp = f"{o.exponent:.2f}" if o.exponent is not None else "n/a"
        flag = ""
        if o.status in ("recursion", "timeout", "error"):
            flag = f"  <== {o.status.upper()}"
        elif o.exponent is not None and o.exponent > 1.5:
            flag = "  <== SUPERLINEAR"
        if flag:
            print(f"{o.family:22}{o.adapter:16}{exp:>9}  {o.status}{flag}")
    print("\n(only superlinear / recursion / timeout rows shown; cmark + "
          "markdown-it-py are the robust baseline)")
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

    p_fuzz = sub.add_parser("fuzz", help="run the differential fuzzing campaign (M2)")
    p_fuzz.add_argument("--iterations", type=int, default=5000)
    p_fuzz.add_argument("--seed", type=int, default=0)
    p_fuzz.add_argument("--out", default="findings", help="output dir (git-ignored)")
    p_fuzz.add_argument("--max-findings", type=int, default=50)
    p_fuzz.add_argument("--no-minimize", action="store_true")
    p_fuzz.add_argument("--drop-version-skew", action="store_true",
                        help="drop divergences flagged as possible version skew")
    p_fuzz.add_argument("--require-offenders", default=None,
                        help="comma-separated parser names that must be among the offenders")
    p_fuzz.set_defaults(func=_cmd_fuzz)

    p_sec = sub.add_parser("security", help="Phase 3 sanitization-bypass scan (spec §6)")
    p_sec.add_argument("--iterations", type=int, default=4000)
    p_sec.add_argument("--seed", type=int, default=0)
    p_sec.set_defaults(func=_cmd_security)

    p_perf = sub.add_parser("perf", help="algorithmic-complexity / DoS scan (spec §3)")
    p_perf.add_argument("--budget", type=float, default=8.0, help="per-input time budget (s)")
    p_perf.set_defaults(func=_cmd_perf)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
