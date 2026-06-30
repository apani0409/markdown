# PR (ready to submit): mistletoe — O(n²) blowup on closing-bracket runs

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0003-Fix-O-n-2-blowup-on-closing-bracket-runs-in-find_cor.patch`](patches/mistletoe/)

> Independent of the crash and list-marker fixes (touches only
> `core_tokens.py` / `test_core_tokens.py`), so it can be filed as its own PR or
> applied alongside. `git am` the patch.

## Suggested PR title

> Fix: O(n²) blowup on closing-bracket runs in `find_core_tokens`

## Suggested PR body

**What** — Inline parsing is quadratic in the number of closing brackets. A few
KB of `]` (or `[a]`) pins the CPU for seconds — an untrusted-input
amplification / DoS vector. cmark and markdown-it-py are linear on the same
input.

```python
import mistletoe, time
for n in (1000, 2000, 4000, 8000):
    s = "]" * n
    t = time.perf_counter(); mistletoe.markdown(s)
    print(n, round(time.perf_counter() - t, 4))
# before:  ~quadratic (exponent ≈ 1.95);  8000 -> ~0.37 s,  growing as O(n²)
# after:   ~linear    (exponent ≈ 0.90);  8000 -> ~0.005 s
```

**Root cause** — `find_core_tokens` caches the next code-span match
(`code_pattern.search`) so it can skip over code spans, but it
*unconditionally* re-ran that **full-string** search after **every** `]`:

```python
elif c == ']':
    i = find_link_image(string, i, delimiters, matches, root)
    code_match = code_pattern.search(string, i)   # O(n) scan, once per ']'
```

On input with many `]` and no code spans, that is one O(n) regex scan per `]`
→ **O(n²)**. (Profiling `']'*8000`: 8001 `re.search` calls = 98% of runtime;
`find_link_image` is negligible.)

**Fix** — only re-scan when the cached match was actually consumed by
`find_link_image` advancing the cursor:

```diff
 elif c == ']':
     i = find_link_image(string, i, delimiters, matches, root)
-    code_match = code_pattern.search(string, i)
+    if code_match is not None and code_match.start() < i:
+        code_match = code_pattern.search(string, i)
```

This is **behaviour-preserving**:
- if the cached match is `None`, a search from a later start can only return
  `None` too (the search space only shrinks);
- if it still starts at/after the cursor, it is exactly what a fresh search from
  the cursor would find;
- only when the cursor has moved *past* the cached match is a re-scan needed.

**Verification** — beyond the reasoning above:
- **0 output diffs** vs unpatched v1.5.1 across the full CommonMark **spec.txt
  (652 examples)** and **12,150** bracket/backtick/code-span/footnote-heavy fuzz
  inputs;
- `]`×n and `[a]`×n go from exponent ≈1.95 to ≈0.90/1.00 (linear);
- full suite: **338 passed, 1 skipped**, no regressions.

**Tests** — added a regression test asserting the number of code-span scans does
not grow with input size (was 101 vs 1001 scans for n=100 vs n=1000; now
constant).

**Scope** — this fixes the closing-bracket family (`]`×n, `[a]`×n), which is the
minimal and most severe form. The *balanced* `[`×n`]`×n and `[](`×n cases have a
second, independent quadratic source (delimiter-list `remove`/`del` by value
inside `find_link_image`/`process_emphasis`) and are left for a separate change.

**Found by** differential algorithmic-complexity measurement vs the cmark
reference.
