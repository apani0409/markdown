# cm-difftest

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![CommonMark](https://img.shields.io/badge/CommonMark-0.31.2-informational)
![tests](https://img.shields.io/badge/tests-pytest-green)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

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
- **M2 — Differential fuzzing** — ✅ **done.** ~1 200 divergences over ~4 000
  inputs, minimized and adversarially triaged into genuine bugs (see
  [`reports/findings-m2.md`](reports/findings-m2.md)). Atheris also surfaced a
  **crash** in mistletoe.
- **M3 — Upstream contribution** — ✅ **ten verified fixes (twelve patches) across all three parsers + more drafts.**
  Ready-to-submit, root-cause patches (validated against each project's own test
  suite) plus issue drafts and CommonMark spec-test proposals in
  [`reports/upstream/`](reports/upstream/) (the actual submission is left to a
  human — this session's GitHub scope is read-only on one repo).

### Verified fixes (root-cause patches, each project's own suite passes)

Ten ready-to-submit fixes ([`reports/upstream/patches/`](reports/upstream/patches/)),
each validated against the target project's test suite:

- **mistletoe** — `IndexError` crash in `process_emphasis` (class of emphasis
  runs; minimal `**"****_*`, 100+ variants). 1-char fix
  (`Delimiter.remove(left=False)`: `type[:n]`→`type[:-n]`). **335 tests pass.**
  [PR](reports/upstream/mistletoe-crash-PR.md)
- **mistletoe** — bare `.`/`)` parsed as an ordered list (`\d{0,9}`→`\d{1,9}`).
  **336 tests pass.** [PR](reports/upstream/mistletoe-list-marker-PR.md)
- **mistletoe** — autolink URI accepted ASCII control chars (`<hs:⇥>` became a
  link); tighten `[^ <>]`→`[^\x00-\x20<>]` to match cmark. **343 tests pass.**
  [PR](reports/upstream/mistletoe-autolink-whitespace-PR.md)
- **mistletoe** — line break in image `alt` dropped/leaked literal chars
  (`![a⏎b]()`→`alt="ab"`); render it as a space, matching cmark. **348 tests
  pass.** [PR](reports/upstream/mistletoe-image-alt-softbreak-PR.md)
- **mistletoe** — **O(n²) emphasis** resolution on long delimiter runs (`*_`×n,
  `*_a`×n): per-closer list-slice copies + O(n) by-value `list.remove`. Pure
  index-based refactor → linear (exp ~1.5→1.1), 0 diffs on spec + 20k fuzz.
  **348 tests pass.** [PR](reports/upstream/mistletoe-emphasis-quadratic-PR.md)
- **mistletoe** — **O(n²) DoS** on bracket runs (three independent causes): a
  full-string code-span rescan on every `]` (`]`×n, `[a]`×n); an O(n)
  reversed-copy + `list.remove` opener lookup (`[`×n`]`×n); and an uncapped
  link-destination paren scan (`[](`×n). All made **linear** (exp ~1.95→0.9–1.1),
  behaviour-preserving (0 diffs on spec.txt + 12k fuzz). The paren cap also fixes
  a conformance bug (>32-deep destinations now match cmark). **342 tests pass.**
  [PR](reports/upstream/mistletoe-quadratic-brackets-PR.md)
- **marko** — `<!` without an ASCII letter started an HTML block (+ dead CDATA
  branch). **1401 tests pass.** [PR](reports/upstream/marko-bang-html-block-PR.md)
- **marko** — lone list marker at EOF → paragraph (allow end-of-input in the
  marker pattern). **1408 tests pass.** [PR](reports/upstream/marko-lone-list-marker-PR.md)
- **markdown-it-py** — image `alt` dropped entities/escapes/code spans/hard breaks
  (`![x&#65;y]`→`alt="xy"`); `renderInlineAsText` now emits `text_special`/
  `code_inline`/`html_inline` + hard breaks. Alt matches cmark; spec 652/652
  unchanged. Found by the hunt in the *most* spec-compliant parser.
  [PR](reports/upstream/markdown-it-py-image-alt-PR.md)
- **marko** — **O(n²) DoS** on `[](`×n: uncapped link-destination paren scan ran
  to EOF on every `]`. Adopt cmark's 32-deep cap → **linear** (exp 1.99→0.93);
  also fixes a conformance bug (>32-deep destinations now match cmark).
  **1412 tests pass.** [PR](reports/upstream/marko-quadratic-paren-PR.md)

Crash-fuzzing summary: marko + markdown-it survived ~1.5 M inputs with **0
crashes**; mistletoe's one crash class is fixed (600 k re-fuzz of the patched
build: 0 new). Security: **0 sanitization bypasses** in 18 k vectors.

### Other findings highlights
- **marko**: lone list marker at EOF (`*` → `<p>*</p>`), unterminated-LRD-title
  discards the definition, block-quote indented-code blank-line handling.
- **markdown-it-py**: lazy continuation after a link reference definition inside
  a block quote; (with marko) unclosed-fence-at-EOF drops the final newline.
- **mistletoe**: soft line break dropped inside image `alt`; bare `)` parsed as a
  list marker; (with marko) trailing tab-bearing line leaks into indented code.
- Two genuinely **under-specified** cases proposed as CommonMark spec tests.
- By-design URL sanitization (`javascript:`) correctly excluded, not filed.

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

## Reports

- [`reports/scorecard.md`](reports/scorecard.md) — M1 compliance scorecard (per parser, per section).
- [`reports/findings-m2.md`](reports/findings-m2.md) — triaged differential findings + the mistletoe crash.
- [`reports/findings-verified.md`](reports/findings-verified.md) — full adversarially-verified catalog (36 cases).
- [`reports/findings-mistletoe.md`](reports/findings-mistletoe.md) — mistletoe deep-dive (6 more bugs + flavor note).
- [`reports/security-phase3.md`](reports/security-phase3.md) — sanitization/XSS posture (0 bypasses in 18k vectors).
- [`reports/performance.md`](reports/performance.md) — algorithmic-complexity / DoS (quadratic + RecursionError in marko/mistletoe; markdown-it-py/cmark robust).
- [`reports/upstream/`](reports/upstream/) — 15 ready-to-file issue drafts + spec-test proposals + standalone reproducer.
- [`docs/analysis.md`](docs/analysis.md) · [`docs/decisions.md`](docs/decisions.md) — analysis log + decision record.

Re-run anything: `cm-difftest scorecard` · `cm-difftest fuzz` · `cm-difftest security` · `cm-difftest perf` · `cm-difftest render "<md>"`.

## Layout

```
cm_difftest/
  normalize/   ported official normalize_html (the safety-critical unit) + spec §4
  corpus/      spec.txt (pinned 0.31.2) + loader
  adapters/    one render(markdown, *, mode) wrapper per parser + cmark reference
  runner/      differential runner with timeout / exception / memory guards
  triage/      classifier + delta-debugging minimizer
  fuzz/        structure-aware generator, campaign, Hypothesis + Atheris targets
  report/      compliance scorecard + findings writers (JSON + Markdown)
  security.py  Phase 3 sanitization-bypass comparison (spec §6)
  cli.py       scorecard / fuzz / security / render / provenance
docs/          analysis log + decision log
scripts/       build_cmark.sh, setup.sh, bootstrap.sh
reports/       scorecard + findings + security report + upstream drafts
tests/         tests for the harness itself (≈140)
findings/      git-ignored until responsibly disclosed (spec §6)
```

## License

MIT.
