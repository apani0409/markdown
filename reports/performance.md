# Performance / algorithmic-complexity findings (DoS class, spec §3)

A parser of untrusted input must not hang, blow up super-linearly, or crash on
nesting depth. This pass measures parse time vs **input size** (length linear in
`n`) and fits a log-log growth exponent; `cmark` 0.31.2 is the robustness
baseline. Reproduce with `cm-difftest perf`.

**markdown-it-py 4.2.0 and cmark 0.31.2 are robust on every family below**
(≈linear, no recursion crash) — so these are implementation problems in marko /
mistletoe, not anything inherent to CommonMark.

## Superlinear (≈quadratic) scaling — amplification / DoS

| Input family | Offender | Growth exponent | Status |
|---|---|---:|---|
| `]`×n | **mistletoe** 1.5.1 | ~1.95 | **fixed** (0003) |
| `[a]`×n | **mistletoe** | ~1.94 | **fixed** (0003) |
| `[`×n + `]`×n | **mistletoe** | ~1.95 | **fixed** (0004) |
| `[](`×n | **mistletoe** | ~1.98 | **fixed** (0005) |
| `[](`×n | **marko** 2.2.3 | ~1.99 | **fixed** ([marko 0003](upstream/patches/marko/)) |
| `[`×n + `]`×n | **marko** | ~2.07 | open (`is_paired` link-text re-scan) |
| `*_`×n | **mistletoe** | ~1.64 (mild) | — |

Quadratic time on linear input is a classic amplification vector: a few kilobytes
of `[[[[…]]]]` or `[](` `[](` … pins a CPU for seconds. cmark and markdown-it-py
stay ≈linear on the same inputs.

### Auto-discovered minimal amplifier (perf-fuzzer)

A perf-fuzzer (`fuzz_amplifiers` — scale random fragments, compare growth
exponents vs the reference) reduced the mistletoe case to **a single repeated
closing bracket**:

```python
import mistletoe, time
s = "]" * 8000
t = time.perf_counter(); mistletoe.markdown(s); print(time.perf_counter() - t)  # ~1.4 s
```

`]`×n → mistletoe **exp ≈ 1.98** (quadratic); markdown-it-py, marko, and cmark
are all ≈linear on it. So mistletoe's quadratic blowup is **general to closing
brackets** (link/bracket resolution rescans on every `]`), not specific to a
nesting shape — the most severe and minimal form. (marko's quadratic is narrower:
the *balanced/nested* `[`×n`]`×n and `[](`×n cases; it is linear on plain `]`×n.)

> **Root-caused + fixed (verified) — all three bracket families now linear.**
> 1. `]`×n, `[a]`×n: `find_core_tokens` cached the next code-span match but
>    re-ran the full-string `code_pattern.search` after *every* `]` — one O(n)
>    scan per `]` → O(n²) (profiling `']'*8000`: 8001 `re.search` calls = 98% of
>    runtime). Guarding the re-scan makes both **linear** (exp ≈0.90/1.00).
> 2. `[`×n`]`×n: `find_link_image` iterated a reversed *copy* of the delimiter
>    list and removed the opener with `list.remove` (O(n) by-value scan) on every
>    `]` (profiling `'['*4000+']'*4000`: `list.remove` = 57% of runtime).
>    Index-based iteration + `del delimiters[i]` makes it **linear** (exp ≈0.99).
> 3. `[](`×n: `match_link_dest` scanned a bare destination counting nested `(`
>    with no depth limit, so a run of never-closing `(` scanned to EOF on every
>    `]` (profiling `'[]('*2000`: `match_link_dest` = 98% of runtime). Adopting
>    cmark's 32-deep paren cap makes it **linear** (exp ≈1.12) *and* fixes a
>    conformance bug (mistletoe parsed >32-deep destinations as links; cmark and
>    the spec treat them as literal text).
>
> All three are behaviour-preserving (**0 output diffs** vs unpatched across
> spec.txt's 652 examples and 12,150 bracket/backtick-heavy fuzz inputs — the
> only change is depth>32 destinations now matching cmark; **342 tests pass**).
> See [`upstream/mistletoe-quadratic-brackets-PR.md`](upstream/mistletoe-quadratic-brackets-PR.md)
> and [`upstream/patches/mistletoe/0003-*.patch`, `0004-*.patch`, `0005-*.patch`](upstream/patches/mistletoe/).

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
