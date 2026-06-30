# Performance / algorithmic-complexity findings (DoS class, spec §3)

A parser of untrusted input must not hang, blow up super-linearly, or crash on
nesting depth. This pass measures parse time vs **input size** (length linear in
`n`) and fits a log-log growth exponent; `cmark` 0.31.2 is the robustness
baseline. Reproduce with `cm-difftest perf`.

**markdown-it-py 4.2.0 and cmark 0.31.2 are robust on every family below**
(≈linear, no recursion crash) — so these are implementation problems in marko /
mistletoe, not anything inherent to CommonMark.

## Superlinear (≈quadratic) scaling — amplification / DoS

| Input family | Offender | Growth exponent | Size to reach ~1 s |
|---|---|---:|---:|
| `[`×n + `]`×n | **marko** 2.2.3 | ~2.07 | ~8 KB |
| `[`×n + `]`×n | **mistletoe** 1.5.1 | ~1.95 | ~16 KB |
| `[](`×n | **mistletoe**, **marko** | ~1.98 (then timeout) | ~12 KB |
| `[a]`×n | **mistletoe** | ~1.94 | ~12 KB |
| `*_`×n | **mistletoe** | ~1.64 (mild) | — |

Quadratic time on linear input is a classic amplification vector: a few kilobytes
of `[[[[…]]]]` or `[](` `[](` … pins a CPU for seconds. cmark and markdown-it-py
stay ≈linear on the same inputs.

## Unbounded recursion — stack overflow on nesting depth

| Input | Offender | Result | Crash size |
|---|---|---|---:|
| `>`×n ` x` (nested block quotes) | **marko** 2.2.3 | `RecursionError` | **~258 bytes** |
| `>`×n ` x` | **mistletoe** 1.5.1 | `RecursionError` | ~514 bytes |

```python
import marko
marko.convert(">" * 300 + " x")   # RecursionError: maximum recursion depth exceeded
```

A **~258-byte** input crashes marko; ~514 bytes crashes mistletoe. On untrusted
input this is an unhandled-crash / DoS. markdown-it-py (which enforces a
`maxNesting` limit) and cmark (iterative, bounded) handle the same input fine.
This is the same class as a parser "must never crash" finding (§3) — deep
nesting must be bounded, not recursed unboundedly.

## Notes / severity

- **High value, security-adjacent.** Algorithmic-complexity and uncontrolled-
  recursion DoS in Markdown parsers are real, recurring (there are CVEs in other
  ecosystems for exactly these). The differential isolates them cleanly: two of
  the four implementations are robust.
- **Fix direction (for maintainers):** the recursion crashes are the most
  actionable — bound block-nesting depth (as markdown-it-py / cmark do) and
  return output or a clean error instead of recursing. The quadratic cases are
  deeper (link/bracket backtracking) and are reported as performance issues.
- Measurements use median-of-3 with a per-input time budget; raw data in
  `findings/perf-raw.json`. Timings are machine-dependent, but the **growth
  exponents** and the **recursion crashes** are stable, machine-independent
  signals.
