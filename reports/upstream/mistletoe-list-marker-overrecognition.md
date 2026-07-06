# [mistletoe] Non-marker punctuation (`.`, `)`) wrongly parsed as an empty list

**Target(s):** miyuchina/mistletoe 1.5.1 · **Python:** 3.11

## Reproducer
```python
import mistletoe
print(mistletoe.markdown("."))   # and ")"
```

- **Expected:** `<p>.</p>\n` (and `<p>)</p>\n`) — cmark + markdown-it-py + marko agree
- **Actual:** `<ul>\n<li></li>\n</ul>\n` for both `.` and `)`

## Spec
List items: an ordered list marker is 1–9 digits followed by `.` or `)`; a bullet marker is `-`/`+`/`*`. A lone `.` or `)` is none of these.

Over-eager list-marker recognition; note the rendered `<ul>` is wrong even if `)`/`.` were a marker (ordered → `<ol>`).


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
