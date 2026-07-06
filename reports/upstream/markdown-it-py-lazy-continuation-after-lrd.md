# [markdown-it-py] Lazy continuation after a link reference definition inside a block quote

**Target(s):** executablebooks/markdown-it-py 4.2.0 (also affects marko 2.2.3) · **Python:** 3.11

## Reproducer
```python
from markdown_it import MarkdownIt
md = MarkdownIt("commonmark")
print(md.render(">[foo]: /url\nbar"))
```

- **Expected:** `<blockquote>\n<p>bar</p>\n</blockquote>\n` (bar stays inside the block quote; cmark + mistletoe agree)
- **Actual:** `<blockquote></blockquote>\n<p>bar</p>\n` (block quote closed early, bar emitted at top level)

## Spec
Block quotes — laziness rule: an unmarked line that would be paragraph-continuation text continues the block quote. After a link reference definition line, `bar` is such a continuation.

Confirmed by `> [foo]: /url\n> bar` rendering with `bar` inside for all parsers — only the *lazy* (no-marker) form diverges. File separately on marko.


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
