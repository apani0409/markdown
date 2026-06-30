# [mistletoe] DoS: RecursionError on nesting depth + quadratic link/bracket parsing

**Target:** miyuchina/mistletoe · **Version:** 1.5.1 · **Python:** 3.11
**Severity:** medium–high (untrusted-input DoS / unhandled crash).

## 1. `RecursionError` on deep block-quote nesting

```python
import mistletoe
mistletoe.markdown(">" * 600 + " x")   # RecursionError: maximum recursion depth exceeded
```

A **~514-byte** input crashes the parser. cmark 0.31.2 and markdown-it-py handle
the same input. Untrusted input → unhandled crash / DoS. Fix direction: bound
block-nesting depth instead of recursing unboundedly.

## 2. Quadratic time on linear input (amplification)

> **Status: two of the three bracket families now have verified fixes** —
> [`mistletoe-quadratic-brackets-PR.md`](mistletoe-quadratic-brackets-PR.md) /
> [`patches/mistletoe/0003-*.patch` + `0004-*.patch`](patches/mistletoe/).
> `]`×n and `[a]`×n (rescan guard, commit 0003) and `[`×n`]`×n (index-based
> opener removal, commit 0004) go from exponent ≈1.95 to ≈0.90–1.00 (linear),
> behaviour-preserving (0 diffs on spec.txt + 12k fuzz inputs), 340 tests pass.
> **Still open:** `[](`×n — a third, independent source (`match_link_dest` scans
> to EOF counting never-closing `(` on every `]`).

Minimal trigger — **a single repeated closing bracket**:

```python
import mistletoe, time
s = "]" * 8000
t = time.perf_counter(); mistletoe.markdown(s); print(time.perf_counter() - t)  # ~1.4 s
```

`]`×n is **~O(n²)** (exponent ≈ 1.98): the link/bracket resolver appears to
rescan on every closing bracket. markdown-it-py, marko, and cmark are ≈linear.

| Input family | Growth exponent | ~size to reach 1 s |
|---|---:|---:|
| `]`×n (minimal) | ~1.98 | ~10 KB |
| `[`×n + `]`×n | ~1.95 | ~16 KB |
| `[](`×n | ~1.98 (then timeout) | ~12 KB |
| `[a]`×n | ~1.94 | ~12 KB |
| `*_`×n | ~1.64 (mild) | — |

```python
import mistletoe, time
s = "[a]" * 12000
t = time.perf_counter(); mistletoe.markdown(s); print(time.perf_counter() - t)  # ~1s+
```

cmark and markdown-it-py stay ≈linear; this is specific to mistletoe's
link/bracket/emphasis handling.

## How it was found

Differential algorithmic-complexity measurement vs the cmark reference. Data:
`reports/performance.md`.

## Duplicate check

No matching issue found via web search; please confirm against the tracker.
