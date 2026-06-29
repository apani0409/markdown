# PR (ready to submit): marko — lone list marker at end of input

**Repo:** frostming/marko · **Base:** v2.2.3 · **Patch:**
[`patches/marko/0002-Fix-a-lone-list-marker-at-end-of-input-starts-an-emp.patch`](patches/marko/)

> Commit **2 of 2** of the marko series (apply after the `<!` fix, or open both
> as one PR / two commits). `git am patches/marko/000*.patch`. Full suite after
> both: **1408 passed**.

## Suggested PR title

> Fix: a lone list marker at end of input starts an empty list item

## Suggested PR body

**What** — A bullet/ordered marker that is the last character of the input (no
trailing newline) was parsed as a paragraph instead of an empty list item:

```python
import marko
marko.convert("*")    # was '<p>*</p>'   now '<ul>\n<li></li>\n</ul>'
marko.convert("-")    # was '<p>-</p>'   now '<ul>\n<li></li>\n</ul>'
marko.convert("1.")   # was '<p>1.</p>'  now '<ol>\n<li></li>\n</ol>'
```

`marko.convert("*\n")` was already correct, so this was an end-of-input edge
case. cmark 0.31.2, markdown-it-py, and mistletoe all produce the empty list.

**Root cause** — `List.pattern` and `ListItem.pattern` in `marko/block.py`
required the marker to be followed by a whitespace character:

```diff
-    pattern = re.compile(r" {,3}(\d{1,9}[.)]|[*\-+])[ \t\n\r\f]")
+    pattern = re.compile(r" {,3}(\d{1,9}[.)]|[*\-+])(?:[ \t\n\r\f]|$)")
```

CommonMark treats a line ending and end-of-input identically (Preliminaries /
"Lines"), so a marker at EOF must be recognized. The `$` only matches at
end-of-buffer, so it cannot make a marker mid-paragraph start a list — verified
that `a\n*` still renders `<p>a\n*</p>` (an empty list item must not interrupt a
paragraph).

**Tests** — added; full suite **1408 passed**, no regressions (incl.
`tests/test_spec.py`).

**Found by** differential testing vs the CommonMark spec + cmark reference.
