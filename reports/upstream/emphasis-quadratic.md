# [mistletoe + marko] DoS: O(n²) emphasis/bracket delimiter resolution

**Targets:** miyuchina/mistletoe 1.5.1, frostming/marko 2.2.3 · **Python:** 3.11
**Severity:** medium (untrusted-input amplification / DoS) · **Status:** mistletoe's pure-emphasis case **fixed & verified** (patch 0008, see below); the bracket×emphasis interleaving and marko's balanced brackets remain (see "What remains").

> **Update — mistletoe pure-emphasis runs are now fixed (verified).** It turned
> out *not* to need a linked-list refactor: the O(n²) came from per-closer list
> *slice copies* (`next_closer`/`matching_opener`) and O(n) *by-value*
> `list.remove`, not from the `openers_bottom` bucketing. A pure index-based
> refactor (`del delimiters[i]`, `range(...)` instead of slices) linearizes
> `*_`×n (1.5→1.1), `*_a`×n (1.67→1.16), `*[`×n (1.8→1.14), behaviour-preserving
> (0 diffs on spec.txt + 20k fuzz, 348 tests). See
> [`mistletoe-emphasis-quadratic-PR.md`](mistletoe-emphasis-quadratic-PR.md) /
> [`patches/mistletoe/0008-*.patch`](patches/mistletoe/).

After the bracket-run quadratics were fixed (mistletoe 0003–0005, marko 0003),
a re-baseline of all input families against the **patched** parsers surfaces a
deeper, shared O(n²) class in the *emphasis*/*delimiter* resolver. cmark 0.31.2
and markdown-it-py are linear on all of these.

## Reproducers (measured on the patched parsers; still superlinear)

| Input family | mistletoe 1.5.1 | marko 2.2.3 |
|---|---:|---:|
| `*_`×n          | ~~1.86~~ → **1.10** (fixed 0008) | ≈1.0 (ok) |
| `*_a`×n         | ~~1.67~~ → **1.16** (fixed 0008) | ≈1.0 (ok) |
| `*[`×n          | ~~1.80~~ → **1.14** (fixed 0008) | ≈1.44 |
| `[*`×n`*]`×n    | ~~2.02~~ → 1.78 (still open) | **timeout** |
| `[`×n`]`×n      | (fixed, 0004) | exp ≈2.10 |

```python
import mistletoe, time
s = "[*" * 2000 + "*]" * 2000          # ~8 KB
t = time.perf_counter(); mistletoe.markdown(s); print(time.perf_counter() - t)  # seconds
```

## Root cause (three contributing O(n) factors, all per closing delimiter)

mistletoe `core_tokens.py` and marko `inline_parser.py` both resolve emphasis
and links over a single Python **list** of delimiters, with several per-element
operations that are each O(n):

1. **Per-call list-slice copies.** mistletoe's `next_closer` iterated
   `delimiters[curr_pos:]` and `matching_opener` iterated
   `delimiters[curr_pos-1:bottom:-1]` — each call copied the scanned span.
   **(mistletoe: fixed in 0008 — index iteration.)**
2. **O(n) `list.remove()` by value.** mistletoe removed spent delimiters with
   `delimiters.remove(x)` (a by-value list scan) once per closer.
   **(mistletoe: fixed in 0008 — `del delimiters[i]` at the known index.)**
   Together (1)+(2) were the *entire* cause of the pure-emphasis quadratic;
   fixing them made `*_`×n / `*_a`×n / `*[`×n linear with **0 behaviour change**.
3. **Backward scan past emphasis delimiters (still open).** For `[*`×n`*]`×n,
   mistletoe's `find_link_image` (and marko's `look_for_image_or_link`) scan
   *backwards through the whole delimiter list* — including all interleaved `*`
   delimiters — to find the matching `[`. cmark avoids this with a *separate*
   bracket stack (`subj->last_bracket`); these parsers keep brackets and emphasis
   in one list.

## What remains (deeper, not patched)

- **mistletoe `[*`×n`*]`×n** and **marko `[`×n`]`×n / `[*`×n`*]`×n** — factor (3),
  the bracket×emphasis interleaving. Making the `[` lookup skip emphasis
  delimiters needs a *separate bracket stack* (as cmark uses), a structural change
  with real regression risk for famously-subtle emphasis rules. Reported with root
  cause rather than shipped.
- Note the earlier assumption that the *whole* class needed a doubly-linked-list
  refactor was **wrong**: the pure-emphasis quadratic (factors 1+2) was fixable
  with a localized, provably-equivalent refactor (patch 0008). Only factor (3)
  needs the bigger change.

## How it was found

Differential algorithmic-complexity re-baseline (growth-exponent fit) across all
input families, run against the *patched* parsers to expose the next layer once
the bracket-run quadratics were removed. Data: `reports/performance.md`.

## Duplicate check

No matching issue found via web search; please confirm against each tracker.
