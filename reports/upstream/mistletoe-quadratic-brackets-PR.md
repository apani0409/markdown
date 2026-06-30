# PR (ready to submit): mistletoe — O(n²) blowup on bracket runs

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patches (three commits):**
[`0003-…-closing-bracket-runs-in-find_core_tokens.patch`](patches/mistletoe/) +
[`0004-…-balanced-bracket-runs-in-find_link_image.patch`](patches/mistletoe/) +
[`0005-…-cap-link-destination-paren-nesting-at-32.patch`](patches/mistletoe/)

> Independent of the crash and list-marker fixes (touches only
> `core_tokens.py` / `test_core_tokens.py`), so it can be filed as its own PR or
> applied alongside. `git am` all three patches.

Three independent O(n²) sources in mistletoe's inline parser conspire to make a
few KB of brackets pin the CPU for seconds (an untrusted-input amplification /
DoS vector). cmark and markdown-it-py are linear on all of these.

| Input family | Before | After |
|---|---:|---:|
| `]`×n            | exp ≈1.95 (O(n²)) | exp ≈0.90 (linear) — commit 0003 |
| `[a]`×n          | exp ≈1.94 (O(n²)) | exp ≈1.00 (linear) — commit 0003 |
| `[`×n`]`×n       | exp ≈1.96 (O(n²)) | exp ≈0.99 (linear) — commit 0004 |
| `[](`×n          | exp ≈1.99 (O(n²)) | exp ≈1.12 (linear) — commit 0005 |

Commit 0005 also fixes a **conformance** divergence: mistletoe parsed link
destinations nested >32 parens deep as links, where cmark (and the spec's
reference parser) treat them as literal text.

---

## Commit 0003 — closing-bracket rescan (`find_core_tokens`)

### Suggested PR title

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

---

## Commit 0004 — opener lookup/removal (`find_link_image`)

### Suggested PR title

> Fix: O(n²) blowup on balanced bracket runs in `find_link_image`

### Suggested PR body

**What** — After the closing-bracket fix, `[`×n`]`×n is still quadratic.

```python
import mistletoe, time
for n in (1000, 2000, 4000, 8000):
    s = "[" * n + "]" * n
    t = time.perf_counter(); mistletoe.markdown(s)
    print(2 * n, round(time.perf_counter() - t, 4))
# before:  exponent ≈ 1.96 (O(n²));  after: exponent ≈ 0.99 (linear)
```

**Root cause** — for every `]`, `find_link_image` iterated a **reversed copy** of
the delimiter list and removed the matched opener with `list.remove` (an O(n)
**by-value** scan):

```python
def find_link_image(string, offset, delimiters, matches, root=None):
    i = len(delimiters) - 1
    for delimiter in delimiters[::-1]:        # O(n) copy, every ']'
        if delimiter.type in ('[', '!['):
            ...
            delimiters.remove(delimiter)      # O(n) by-value scan
            return offset
        i -= 1
```

With `[`×n`]`×n the opener sits at the end of the list, so each close pays O(n)
to copy + O(n) to scan-and-remove → **O(n²)**. (Profiling `'['*4000+']'*4000`:
`list.remove` = 57% of runtime.)

**Fix** — iterate by index from the end and delete the opener by index:

```diff
-    i = len(delimiters) - 1
-    for delimiter in delimiters[::-1]:
+    for i in range(len(delimiters) - 1, -1, -1):
+        delimiter = delimiters[i]
         if delimiter.type in ('[', '!['):
             if not delimiter.active:
-                delimiters.remove(delimiter)
+                del delimiters[i]
                 return offset
             ...
-            delimiters.remove(delimiter)
+            del delimiters[i]
             return offset
-        i -= 1
```

`i` is exactly the index the old loop computed and already passed to
`process_emphasis(string, i, …)` / `deactivate_delimiters(delimiters, i, '[')`,
so the change is **behaviour-preserving**; deleting the end-of-list opener is
O(1) → linear.

**Verification** — **0 output diffs** vs unpatched v1.5.1 across spec.txt (652)
and 12,150 bracket-heavy fuzz inputs; `[`×n`]`×n drops from exp ≈1.96 to ≈0.99.
Full suite: **340 passed, 1 skipped**.

**Tests** — added a min-of-3 timing-ratio regression test (4× the input must not
multiply time by ~16×; original ≈14.7× vs fixed ≈3.3×) plus link/image bracket
correctness tests covering the index-based removal paths.

---

## Commit 0005 — link-destination paren cap (`match_link_dest`)

### Suggested PR title

> Fix: cap link-destination paren nesting at 32 (matches cmark; fixes O(n²) on `[](`×n)

### Suggested PR body

**What** — `[](`×n is quadratic, *and* destinations nested >32 parens deep are
mis-parsed as links.

```python
import mistletoe, time
for n in (1000, 2000, 4000, 8000):
    s = "[](" * n
    t = time.perf_counter(); mistletoe.markdown(s)
    print(3 * n, round(time.perf_counter() - t, 4))
# before:  exponent ≈ 1.99 (O(n²));  after: exponent ≈ 1.1 (linear)

# conformance: a destination nested 33 deep
md = "[a](" + "(" * 33 + "x" + ")" * 33 + ")"
# cmark 0.31.2: literal text (not a link);  mistletoe before: <a href=…> (wrong)
```

**Root cause** — `match_link_dest` scans a bare (non-`<>`) destination counting
nested `(`/`)` with **no depth limit**. For `[](`×n (a run of unbalanced `(`
with no closing `)`) the counter never returns to zero, so every `]` scans to
end-of-input → **O(n²)** (profiling `'[]('*2000`: `match_link_dest` = 98% of
runtime).

**Fix** — adopt the same cap as CommonMark's reference parser
(`cmark`’s `manual_scan_link_url_2`: `if (nb_p > 32) return -1;`). mistletoe's
`count` starts at 1 for the link's own `(`, so depth >32 ⇔ `count > 33`:

```diff
                 if c == '(':
                     count += 1
+                    if count > 33:
+                        return None
                 elif c == ')':
                     count -= 1
```

This bounds the scan to ~32 characters per `]` (→ linear) **and** makes
mistletoe agree with cmark on deep nesting.

**Verification** — patched mistletoe agrees with cmark at destination paren
depths **1…100** (boundary exactly at 32/33); **0 output diffs** vs original
across spec.txt (652) and 12k bracket-heavy fuzz inputs (which never nest >32
deep); `[](`×n drops from exp ≈1.99 to ≈1.12. Full suite: **342 passed, 1
skipped**.

**Tests** — added a 32/33-boundary conformance test and a linear-scaling test
for `[](`×n.

---

**Found by** differential algorithmic-complexity measurement vs the cmark
reference.
