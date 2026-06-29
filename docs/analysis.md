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

## 6. Milestone status

- **M1 — harness + scorecard:** in progress.
- **M2 — differential fuzzing:** not started (gated on M1 zero-false-positive).
- **M3 — upstream contribution:** not started.
