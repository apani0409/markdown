# cm-difftest

**A differential conformance + fuzzing harness for pure-Python CommonMark parsers.**

cm-difftest compares how multiple actively-maintained, CommonMark-compliant
Python Markdown parsers render the same input, flags disagreements, and triages
them into real, reproducible findings — measured against an objective oracle (the
official CommonMark `spec.txt` and the `cmark` C reference), not opinion.

> Honest framing: the *technique* (differential parser fuzzing) is well-established
> and not novel. The value here is concrete — a current compliance picture for
> these parsers, real bugs surfaced and minimized, and a reusable harness.

## Status

Built in strict milestone order (see [`docs/analysis.md`](docs/analysis.md)):

- **M1 — Harness + compliance scorecard** — ✅ **done.** Full `spec.txt` runs
  across all SUTs + the cmark reference with **zero normalization false
  positives** (reference fidelity 652/652). Scorecard below.
- **M2 — Differential fuzzing** — next (M1's criterion is met).
- **M3 — Upstream contribution** — pending.

## Parsers under test

| Role | Package | Version | Target CommonMark |
|---|---|---|---|
| SUT | [markdown-it-py](https://github.com/executablebooks/markdown-it-py) | 4.2.0 | 0.31.2 |
| SUT | [mistletoe](https://github.com/miyuchina/mistletoe) | 1.5.1 | recorded at runtime |
| SUT | [marko](https://github.com/frostming/marko) | 2.2.3 | 0.31.2 |
| Reference | [cmark](https://github.com/commonmark/cmark) (built from source) | 0.31.2 | 0.31.2 |

Spec corpus pinned to **CommonMark 0.31.2**. See [`docs/analysis.md`](docs/analysis.md)
for why other parsers (commonmark.py, Python-Markdown, mistune) are excluded.

## Setup

```bash
bash scripts/setup.sh          # venv + pinned deps + build cmark 0.31.2
source .venv/bin/activate
pytest -q                      # run the harness's own test suite
```

`scripts/build_cmark.sh` builds the `cmark` C reference at tag 0.31.2 (the C
toolchain `cmake` + a C compiler are required). No pip binding ships exactly
0.31.2, so the reference is compiled to match the pinned spec version (spec §5).

`scripts/bootstrap.sh` is an idempotent setup (venv + deps + cmark, building only
what's missing) — handy for a fresh checkout or to wire into a Claude Code
`SessionStart` hook.

## Compliance scorecard

Per-parser pass/fail against the official CommonMark **0.31.2** `spec.txt` (652
examples), compared after the official `normalize_html`. Full breakdown in
[`reports/scorecard.md`](reports/scorecard.md) (regenerate with
`cm-difftest scorecard`).

| Parser | Version | Passed | Pass rate |
|---|---|---:|---:|
| markdown-it-py | 4.2.0 | 652 / 652 | **100.0%** |
| marko | 2.2.3 | 652 / 652 | **100.0%** |
| mistletoe | 1.5.1 | 628 / 652 | 96.3% |
| cmark *(reference)* | 0.31.2 | 652 / 652 | 100.0% |

**M1 criterion met:** the reference matches `spec.txt` on 652/652 examples →
normalizer false-positive rate **0.0%**. mistletoe's 24 gaps are genuine
disagreements (clustered in Raw HTML, Emphasis, and Link reference definitions),
not formatting artifacts — the differential-fuzzing seed list for M2.

## Layout

```
cm_difftest/
  normalize/   ported official normalize_html (the safety-critical unit) + spec §4
  corpus/      spec.txt (pinned 0.31.2) + loader
  adapters/    one render(markdown, *, mode) wrapper per parser + cmark reference
  runner/      differential runner with timeout / exception / memory guards
  report/      compliance scorecard + findings writers (JSON + Markdown)
docs/          analysis log + decision log
scripts/       build_cmark.sh, setup.sh
tests/         tests for the harness itself
findings/      git-ignored until responsibly disclosed (spec §6)
```

## License

MIT.
