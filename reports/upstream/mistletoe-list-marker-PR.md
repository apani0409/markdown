# PR (ready to submit): mistletoe — bare `.`/`)` parsed as an ordered list

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0002-Fix-a-bare-.-or-must-not-be-parsed-as-an-ordered-lis.patch`](patches/mistletoe/)

> Independent of the crash fix (touches `block_token.py`, not `core_tokens.py`),
> so it can be filed as its own PR or applied alongside. `git am` the patch.

## Suggested PR title

> Fix: a bare `.` or `)` must not be parsed as an ordered list

## Suggested PR body

**What** — A lone `.` or `)` was rendered as an empty ordered list:

```python
import mistletoe
mistletoe.markdown(".")   # was '<ul>\n<li></li>\n</ul>'   now '<p>.</p>'
mistletoe.markdown(")")   # was '<ul>\n<li></li>\n</ul>'   now '<p>)</p>'
```

(cmark, markdown-it-py, and marko all produce the paragraph. Note the old output
was also doubly wrong — `<ul>` for an *ordered* marker.)

**Root cause** — `List.pattern` and `ListItem.pattern` used `\d{0,9}[.)]`,
allowing **zero** digits, so `.`/`)` matched as an ordered marker:

```diff
-    pattern = re.compile(r' {0,3}(?:\d{0,9}[.)]|[+\-*])(?:[ \t]*$|[ \t]+)')
+    pattern = re.compile(r' {0,3}(?:\d{1,9}[.)]|[+\-*])(?:[ \t]*$|[ \t]+)')
...
-    pattern = re.compile(r'( {0,3})(\d{0,9}[.)]|[+\-*])($|\s+)')
+    pattern = re.compile(r'( {0,3})(\d{1,9}[.)]|[+\-*])($|\s+)')
```

CommonMark requires **1–9 digits** before the `.`/`)` delimiter.

**Tests** — added (the existing `test_parse_marker` bad-line list missed `.`/`)`).
Full suite: **336 passed, 1 skipped**, no regressions.

**Found by** differential testing vs the CommonMark spec + cmark reference.
