# Decision log

Lightweight ADR-style record of binding decisions. Newest first within each
milestone. Each entry: context → decision → consequences.

## M1

### D-007 — Faithful Python-3 port of the official normalizer
**Context:** The official `test/normalize.py` is Python-2-flavoured (`urllib.quote`)
and contains a near-dead branch (`if v in ('href','src')`, testing the value).
**Decision:** Port to Python 3 with minimal changes (`urllib.parse`), preserving
behaviour verbatim — including the quirk — so our verdicts match the spec
runner's. Ship the official doctests in our test suite.
**Consequences:** Our "compliant" verdict means exactly what the spec project's
own conformance comparison means.

### D-006 — Adapter `mode` enum: RAW vs SAFE
**Context:** Parsers differ on raw HTML / dangerous URLs by default (§6).
**Decision:** Every adapter takes `mode ∈ {RAW, SAFE}`. RAW (raw HTML allowed)
matches `spec.txt` and is the default for M1/M2. SAFE (sanitised) is for the
Phase 3 security comparison only. Never mix modes in one comparison.
**Consequences:** For cmark, RAW = `CMARK_OPT_UNSAFE`, SAFE = default options.

### D-005 — cmark obtained via release tarball, not `git clone`
**Context:** The agent proxy blocks `git clone github.com` (403) but allows
release tarballs over HTTPS and `raw.githubusercontent.com`.
**Decision:** `scripts/build_cmark.sh` downloads
`.../cmark/archive/refs/tags/0.31.2.tar.gz` and builds it.
**Consequences:** Reproducible offline-ish build; no dependency on git access.

### D-004 — cmark binding via ctypes against built shared lib
**Context:** Need an exact, reasonably fast 0.31.2 oracle (M2 fuzzes millions of
inputs).
**Decision:** Build `libcmark.so` (`BUILD_SHARED_LIBS=ON`) and call
`cmark_markdown_to_html(text, len, opts)` via `ctypes` in-process.
**Consequences:** Fast, exact 0.31.2; the CLI binary is also available for
cross-checking.

### D-003 — Pace: pause per milestone *(user decision)*
**Decision:** Work autonomously within a milestone (commit per component); stop
to review at the M1/M2/M3 boundaries; surface genuine decisions as they arise.

### D-002 — Documentation language: English *(user decision)*
**Decision:** Committed artifacts (README, scorecard, analysis, this log) are in
English (OSS/portfolio audience, §12). Plus a running analysis + decision log.

### D-001 — cmark reference: build 0.31.2 from source *(user decision)*
**Context:** No pip binding bundles 0.31.2; target spec version is 0.31.2 (§5).
**Decision:** Build the C reference at tag 0.31.2; keep `paka.cmark` (0.30.2) as a
recorded secondary fallback.
**Consequences:** Highest oracle fidelity; adds a one-time C build step
(`scripts/build_cmark.sh`).
