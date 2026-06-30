# [mistletoe + marko] DoS: O(n²) emphasis/bracket delimiter resolution

**Targets:** miyuchina/mistletoe 1.5.1, frostming/marko 2.2.3 · **Python:** 3.11
**Severity:** medium (untrusted-input amplification / DoS) · **Status:** root-caused, **not** patched (see "Why not fixed here").

After the bracket-run quadratics were fixed (mistletoe 0003–0005, marko 0003),
a re-baseline of all input families against the **patched** parsers surfaces a
deeper, shared O(n²) class in the *emphasis*/*delimiter* resolver. cmark 0.31.2
and markdown-it-py are linear on all of these.

## Reproducers (measured on the patched parsers; still superlinear)

| Input family | mistletoe 1.5.1 | marko 2.2.3 |
|---|---:|---:|
| `*_`×n          | exp ≈1.86 | ≈1.0 (ok) |
| `*[`×n          | exp ≈1.80 | ≈1.44 |
| `[*`×n`*]`×n    | exp ≈2.02 | **timeout** |
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

1. **Per-call list-slice copies.** mistletoe's `next_closer` iterates
   `delimiters[curr_pos:]` and `matching_opener` iterates
   `delimiters[curr_pos-1:bottom:-1]` — each call copies the scanned span. On a
   long delimiter run (`*_`×n) this alone is O(n²).
   *(A safe slice→index rewrite verified 0 output diffs on spec.txt + 12k fuzz
   and lowers `*_`×n from exp ≈1.86 to ≈1.25 — but does not by itself linearize
   the family, because of (2) and (3).)*
2. **O(n) `list.remove()` / `del list[i]` by value/shift.** Both parsers remove
   spent delimiters from the middle of the list (`delimiters.remove(opener)` /
   `del delimiters[…]`), each O(n).
3. **Backward scan past emphasis delimiters.** For `[*`×n`*]`×n, mistletoe's
   `find_link_image` (and marko's `look_for_image_or_link`) scan *backwards
   through the whole delimiter list* — including all interleaved `*` delimiters —
   to find the matching `[`. cmark avoids this with a *separate* bracket stack
   (`subj->last_bracket`); these parsers keep brackets and emphasis in one list.

## Why this is not fixed here

The CommonMark reference (cmark) keeps emphasis/link resolution linear by using a
**doubly-linked list** of delimiters plus a *separate* bracket stack, so removals
are O(1) and the bracket lookup never walks emphasis delimiters. Reproducing that
in mistletoe/marko is a **structural refactor** of the inline parser, not a
localized change — high regression risk for a parser whose emphasis rules are
famously subtle. The conservative, verifiable wins (the bracket-run fixes) were
shipped; this deeper class is reported with its root cause so maintainers can
decide on the larger change. The slice→index micro-optimization in (1) is
available as a safe partial mitigation if wanted.

## How it was found

Differential algorithmic-complexity re-baseline (growth-exponent fit) across all
input families, run against the *patched* parsers to expose the next layer once
the bracket-run quadratics were removed. Data: `reports/performance.md`.

## Duplicate check

No matching issue found via web search; please confirm against each tracker.
