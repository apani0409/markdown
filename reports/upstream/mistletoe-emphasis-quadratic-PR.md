# PR (ready to submit): mistletoe — O(n²) emphasis resolution on long delimiter runs

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0008-Fix-O-n-2-emphasis-resolution-on-long-delimiter-runs.patch`](patches/mistletoe/)

> Independent of the other fixes (touches only `core_tokens.py` /
> `test_core_tokens.py`). `git am` the patch.

## Suggested PR title

> Fix: O(n²) emphasis resolution on long delimiter runs

## Suggested PR body

**What** — Inline emphasis parsing is superlinear in the number of emphasis
delimiters. A few KB of emphasis markers pins the CPU (an untrusted-input
amplification / DoS vector); cmark and markdown-it-py are linear on the same
inputs.

```python
import mistletoe, time
for n in (1000, 2000, 4000, 8000):
    s = "*_" * n
    t = time.perf_counter(); mistletoe.markdown(s)
    print(2 * n, round(time.perf_counter() - t, 4))
# before: exponent ≈ 1.5 ('*_'*n) to ≈1.67 ('*_a'*n);  after: ≈1.1 (linear)
```

**Root cause** — `process_emphasis` and its helpers do two O(n) operations *per
closing delimiter*, so a run of n delimiters is O(n²):

1. `next_closer` and `matching_opener` scan **list slices**
   (`delimiters[curr_pos:]` and `delimiters[curr_pos - 1:bottom:-1]`), which copy
   the scanned span on every call;
2. `process_emphasis` removes each spent delimiter with
   `delimiters.remove(x)` — an O(n) **by-value** search of the list.

**Fix** — iterate by index and delete by the already-known index:

```diff
 def next_closer(curr_pos, delimiters):
-    for i, delimiter in enumerate(delimiters[curr_pos:], start=curr_pos or 0):
+    for i in range(curr_pos or 0, len(delimiters)):
+        delimiter = delimiters[i]
         if hasattr(delimiter, 'close') and delimiter.close:
             return i
     return None

 def matching_opener(curr_pos, delimiters, bottom):
     if curr_pos > 0:
         curr_delimiter = delimiters[curr_pos]
-        index = curr_pos - 1
-        for delimiter in delimiters[curr_pos - 1:bottom:-1]:
+        stop = -1 if bottom is None else bottom
+        for index in range(curr_pos - 1, stop, -1):
+            delimiter = delimiters[index]
             if (hasattr(delimiter, 'open') and delimiter.open
                     and delimiter.closed_by(curr_delimiter)):
                 return index
-            index -= 1
     return None
```

and in `process_emphasis`, replace the three `delimiters.remove(opener|closer)`
calls with `del delimiters[open_pos]` / `del delimiters[curr_pos]` (the index is
already known at each site).

This is a **pure refactor**: same iteration order, and since the delimiters are
unique objects, `remove`-by-value and `del`-by-index delete exactly the same
element. It removes the O(n)-per-closer factor while leaving behaviour unchanged.

**Verification** — **0 output diffs** vs the previous behaviour across the
CommonMark spec.txt (652 examples) and **20,000** emphasis/bracket-heavy fuzz
inputs; `*_`×n drops from exp ≈1.5 to ≈1.1, `*_a`×n from ≈1.67 to ≈1.16,
`*[`×n from ≈1.8 to ≈1.14. Full suite: **348 passed, 1 skipped**.

**Tests** — added a min-of-3 timing-ratio regression test (`*_`×n, 4× input
must not multiply time ~16×).

**Scope** — this covers the pure emphasis-delimiter runs. One pathological
*bracket×emphasis* interleaving (`[*`×n`*]`×n) remains superlinear from a
different source (`find_link_image` scanning back through emphasis delimiters to
find the matching `[`); cmark avoids that with a separate bracket stack, a deeper
change left for separate work.

**Found by** differential algorithmic-complexity measurement vs the cmark
reference.
