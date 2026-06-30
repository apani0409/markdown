# [marko] DoS: RecursionError on nesting depth + quadratic link/bracket parsing

**Target:** frostming/marko · **Version:** 2.2.3 · **Python:** 3.11
**Severity:** medium–high (untrusted-input DoS / unhandled crash).

## 1. `RecursionError` on deep block-quote nesting (tiny payload)

```python
import marko
marko.convert(">" * 300 + " x")   # RecursionError: maximum recursion depth exceeded
```

A **~258-byte** input crashes the parser with an unhandled `RecursionError`.
cmark 0.31.2 and markdown-it-py (which enforces a `maxNesting` limit) render the
same input fine. On untrusted input this is an unhandled crash / DoS.

**Fix direction:** bound block-nesting depth and return output or a clean error
instead of recursing unboundedly (markdown-it uses `maxNesting`; cmark is
iterative).

## 2. Quadratic time on linear input (amplification)

Parse time grows ~O(n²) while input length is linear:

| Input family | Growth exponent | Status |
|---|---:|---|
| `[](`×n | ~1.99 | **verified fix** — [PR](marko-quadratic-paren-PR.md) / [`patches/marko/0003-*.patch`](patches/marko/) |
| `[`×n + `]`×n | ~2.07 | open (independent source: `is_paired` re-scans link text) |

```python
import marko, time
s = "[" * 8000 + "]" * 8000
t = time.perf_counter(); marko.convert(s); print(time.perf_counter() - t)  # ~1s+
```

cmark and markdown-it-py stay ≈linear on the same inputs, so this is specific to
marko's link/bracket handling, not inherent to CommonMark.

> **`[](`×n fixed (verified).** `_parse_link_dest_title` scanned a bare link
> destination counting nested `(` with no limit → `[](`×n scanned to EOF on every
> `]` (O(n²); `_parse_link_dest_title` = 80% of runtime). Adopting cmark's 32-deep
> paren cap makes it **linear** (exp ≈0.93) *and* fixes a conformance bug (marko
> parsed >32-deep destinations as links; cmark/spec treat them as literal text).
> Verified: agrees with cmark at depths 1–100; 0 diffs vs original on spec.txt +
> 12k fuzz; **1412 tests pass**. `[`×n`]`×n remains open (the `is_paired` link-text
> re-scan is a deeper change with no spec cap analogue).

## How it was found

Differential algorithmic-complexity measurement across the maintained Python
CommonMark parsers + the cmark reference (growth-exponent fit). Data:
`reports/performance.md`.

## Duplicate check

No matching issue found via web search; please confirm against the tracker.
