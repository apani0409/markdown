# Analysis log

A running record of the analysis behind cm-difftest. Updated as each component
lands. The companion document [`decisions.md`](./decisions.md) records the
binding decisions; this file records the *reasoning* and *findings*.

## 0. What we are building (restated from the spec)

A harness that systematically compares how multiple CommonMark parsers render
the same Markdown, flags disagreements, triages them into real findings, and
turns findings into upstream contributions. The value is concrete (real bugs,
upstream PRs, a current compliance picture, a reusable harness) — the technique
(differential parser fuzzing) is well-established and **not** claimed as novel.

Two evaluation regimes:

- **A. Static corpus** — `spec.txt` ships `(markdown, expected_html)` pairs. A
  parser is non-compliant on an example iff `normalize(out) != normalize(expected)`.
  Deliverable: a per-parser compliance scorecard.
- **B. Dynamic / fuzzed** — no expected output exists. Run all SUTs + the `cmark`
  reference; a divergence = ≥2 implementations produce different `normalize(out)`;
  `cmark` is the tiebreaker for "likely-buggy".

## 1. Environment findings (2026-06-29)

| Item | Result |
|---|---|
| Python | 3.11.15 |
| Network to PyPI | OK (`pip install` works) |
| Network to `raw.githubusercontent.com` | OK (fetched spec.txt, normalize.py) |
| Network: `git clone github.com` | **Blocked** (HTTP 403 via agent proxy) |
| Network: GitHub release tarballs (`codeload`) | OK (fetched cmark-0.31.2.tar.gz) |
| C toolchain | gcc 13.3, cmake 3.28.3, make — present |

Consequence: cmark is obtained via the **release tarball**, not `git clone`
(see `scripts/build_cmark.sh`).

## 2. Systems under test (SUT) and the reference oracle

All SUTs are pure-Python, CommonMark-targeting, actively maintained.

| Role | Package | Version | Target spec | How invoked |
|---|---|---|---|---|
| SUT | markdown-it-py | 4.2.0 | **0.31.2** (string found in `html_blocks.py`) | `MarkdownIt("commonmark")` |
| SUT | mistletoe | 1.5.1 | *to confirm at adapter time* | default HTML renderer |
| SUT | marko | 2.2.3 | **0.31.2** (explicit) | default `Markdown()` |
| Reference | cmark (built) | **0.31.2** | 0.31.2 | ctypes -> `libcmark.so` |
| Fallback ref | paka.cmark | 2.3.0 → cmark **0.30.2** | 0.30 | in-process (skew caveat) |
| Fallback ref | cmarkgfm | 2025.10.22 → cmark-gfm **0.29.0.gfm.2** | 0.29 | plain mode only |

**Excluded (with reasons, per spec §2):** `commonmark`/commonmark.py (deprecated,
archived, old spec → version-artifact noise); `Python-Markdown` and `mistune`
(not CommonMark-compliant — comparing them yields design divergence, not bugs).

### 2.1 The cmark version problem (spec §5)

The target spec version is **0.31.2**, but **no pip-installable Python binding
bundles 0.31.2**:

- `paka.cmark` 2.3.0 → cmark **0.30.2**
- `cmarkgfm` 2025.10.22 → cmark-gfm **0.29.0.gfm.2** (a GFM fork, base 0.29)

Differences between 0.29 → 0.30 → 0.31.2 would surface as "disagreements" that
are *version artifacts, not bugs*. Since the C toolchain is available, we build
the exact **cmark 0.31.2** from source and bind it via `ctypes`
(`cmark_markdown_to_html`). This satisfies §5 ("pin a cmark build whose
conformance level matches the chosen spec version") exactly. The pip bindings
are kept as recorded, secondary fallbacks only.

## 3. Critical subtlety #1 — HTML normalization (spec §4)

Comparing raw HTML strings produces massive false positives. We **port the
official `normalize_html`** from `commonmark/commonmark-spec` (`test/normalize.py`,
tag 0.31.2) rather than inventing one, so our compliant/non-compliant verdicts
match the spec's own conformance semantics.

Faithful-port notes (the official file is Python-2-flavoured):
- `urllib.quote`/`unquote` → `urllib.parse.quote`/`unquote` (Py3).
- Preserve the official quirk `if v in ('href', 'src')` (a near-dead branch —
  it tests the attribute *value*, not the key). Changing it to `k` would make
  our normalization diverge from the spec runner's, so we keep it verbatim.
- Behaviour (whitespace collapse, block-tag trimming, self-closing→open,
  attribute sort, charref→unicode except `< > & "`) is otherwise identical; the
  official doctests are run as part of our test suite.

The M1 done-criterion depends entirely on this: running the full corpus must
yield **zero false-positive divergences attributable to normalization**.

## 4. Critical subtlety #2 — spec-version alignment (spec §5)

- `spec.txt` pinned to **0.31.2**.
- Every report records each SUT's library version + target spec version, the
  spec.txt version, and the cmark/binding version.
- Triage gate (M2+): before filing, confirm a divergence is not explained by a
  spec-version difference. If parsers genuinely target different versions and the
  divergence is on a changed feature → classify "version skew — not a bug".

## 5. Subtlety #3 — security / escaping mode (spec §6, Phase 3)

Each parser handles raw HTML and dangerous URL schemes differently by default,
so comparisons must be apples-to-apples. We model an explicit **mode** on every
adapter:

- `RAW` — raw HTML passed through, URLs not sanitized. This is the mode that
  **matches `spec.txt`** (whose expected output preserves raw HTML) and is the
  default for M1 compliance and M2 differential fuzzing. For cmark this means
  `CMARK_OPT_UNSAFE`.
- `SAFE` — raw HTML escaped/stripped, dangerous URLs neutralised. Used only for
  the Phase 3 security comparison. For cmark this is the default options (0),
  which emits `<!-- raw HTML omitted -->` and blanks `javascript:` hrefs.

Verified via ctypes against built cmark 0.31.2:
```
RAW  : '*hi* <script>x</script> [a](javascript:alert(1))'
       -> '<p><em>hi</em> <script>x</script> <a href="javascript:alert(1)">a</a></p>'
SAFE : -> '<p><em>hi</em> <!-- raw HTML omitted -->x<!-- raw HTML omitted --> <a href="">a</a></p>'
```

Disclosure discipline: security-relevant findings go to maintainers privately
first and live only in the git-ignored `findings/` directory until disclosed.

## 6. M1 results (2026-06-29)

The harness runs the full corpus in ~1 s. Scorecard (`reports/scorecard.*`):

| Parser | Version | Passed / 652 | Pass rate |
|---|---|---:|---:|
| markdown-it-py | 4.2.0 | 652 | 100.0% |
| marko | 2.2.3 | 652 | 100.0% |
| mistletoe | 1.5.1 | 628 | 96.3% |
| cmark (ref) | 0.31.2 | 652 | 100.0% |

**M1 done-criterion — met.** Reference fidelity is 652/652, so the normalizer
false-positive rate is **0.0%**, and zero comparisons are classified as
normalization artifacts. Crucially, three *independent* implementations
(cmark, markdown-it-py, marko) all reach 100% through the same normalizer — if
the normalizer were collapsing real differences or leaving formatting noise,
they could not all be perfect. This is the objective evidence that reported
divergences are genuine.

mistletoe 1.5.1's 24 failures (all `spec_noncompliance`, all flagged
`possible_version_skew` because mistletoe declares no spec version) cluster as:

| Section | fails | Section | fails |
|---|---:|---|---:|
| Emphasis and strong emphasis | 7 | Backslash escapes | 2 |
| Raw HTML | 6 | Entity/numeric char refs | 2 |
| Link reference definitions | 3 | Setext / Code spans / Links / Images | 1 each |

Failing example numbers: 12, 14, 27, 41, 91, 209, 210, 211, 343, 352, 354, 359,
363, 380, 385, 395, 508, 590, 619, 620, 624, 625, 626, 632. These are the
high-value seeds for M2 differential fuzzing and M3 triage (each must still pass
the version-skew gate before any upstream filing).

## 7. M2 results — differential fuzzing

The structure-aware fuzzer (`cm_difftest/fuzz`) seeds from the spec.txt examples
and applies weighted, syntax-level mutations; the campaign runs each input
through all parsers + cmark, keeps genuine divergences, dedupes by a structural
signature, and minimizes each with ddmin.

Signal (8 seeds, ~4 k inputs after early-stop at 40 findings/seed):
**~1 220 divergences, 0 crashes, 201 distinct minimized findings.** Zero crashes
is the expected outcome for hardened parsers (spec §8) — the value is the
*differential* signal.

A high-precision filter (cmark agrees with ≥1 other parser **and** an offender
targets 0.31.2 **and** not a URL-scheme case) yields **103 strong candidates in
24 root-cause clusters**. Confirmed genuine bugs (cmark + the spec + ≥1 other
impl agree; offender targets 0.31.2 → no version-skew):

| Offender | Minimal input | Bug | Spec area |
|---|---|---|---|
| marko | `*` / `-` / `1.` | lone list marker at EOF → paragraph, not empty list item | List items |
| marko | `<!` | treated as a raw HTML block instead of escaped text | HTML blocks |
| marko | `[](;)` | URL sub-delimiter `;` over-percent-encoded (`%3B`) | Links |
| marko | `` [`]`]() `` | code span inside link label breaks link parsing | Links / code spans |
| markdown-it-py | `` [`t`>` `` | code span not recognized in this context | Code spans |
| marko + mistletoe | `-\xa0--` | `-`<NBSP>`--` parsed as thematic break (NBSP is not a valid space) | Thematic breaks |

marko's lone-marker and `<!` bugs belong to a documented family (its CHANGELOG
shows v2.1.4 "Correct the parsing of LinkRefDef if it is the last line but
doesn't end with a line break" and v2.2.3 "Fix an infinite loop caused by
unnormalized line breaks") — our cases are new instances not yet fixed in 2.2.3
and not in its issue tracker. These are regression-pinned in
`tests/test_findings_regression.py`.

Candidates deliberately classified **not a clean bug** and excluded:
URL-scheme handling (`javascript:`, `data:`) where markdown-it sanitizes by
design and marko rewrites to `#harmful-link` (security comparison territory,
Phase 3 — handled separately, not as correctness bugs); and exact percent-
encoding of some URL characters where the spec under-specifies.

**M2 done-criterion — met.** ≥1 genuine divergence beyond the static corpus,
triaged (not version-skew, not normalization), minimized, with the likely-wrong
implementation identified — in fact several, across two 0.31.2-targeting parsers.

### 7.1 Crash class (Atheris) and adversarial verification

The in-process differential campaign found **0 crashes**, but the **Atheris**
coverage-guided target surfaced a genuine **mistletoe crash** after ~262 k
executions: `****"************+****` → `IndexError` in
`core_tokens.process_emphasis` (`closer.type[0]` on an empty `type`); minimized
with ddmin to a 1-minimal 22-char input. markdown-it-py, marko, and cmark all
render it. This is the campaign's highest-severity finding and vindicates running
both generation sources (spec §8). (An earlier Atheris run also caught a decode
bug in our *own* target — now fixed and tested.)

All candidate divergences were put through an **adversarial verification** pass
(one agent per case, reasoning from the spec text, cmark as a strong-but-not-
absolute tiebreaker). The human gate then overrode one agent verdict: for
`[r]:/\n*` the agent called cmark buggy, but the spec appendix supports cmark's
paragraph-buffering model, so we classify it **spec-ambiguous**, not a cmark bug
(§5 in action: the reference can be on a debatable side). Full triaged results in
`reports/findings-m2.md`; upstream drafts in `reports/upstream/`.

## 8. Milestone status

- **M1 — harness + scorecard:** ✅ done (criterion met, scorecard shipped).
- **M2 — differential fuzzing:** ✅ done (genuine minimized findings + a crash,
  adversarially triaged).
- **M3 — upstream contribution:** ✅ drafts ready (issue drafts + spec-test
  proposals in `reports/upstream/`; filing requires repo write access /
  maintainer contact, left to a human).
