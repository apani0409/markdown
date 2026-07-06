# [marko] Unterminated title discards the whole link reference definition

**Target(s):** frostming/marko 2.2.3 · **Python:** 3.11

## Reproducer
```python
import marko
print(marko.convert('[foo]: /url\n"unterminated'))
```

- **Expected:** `<p>&quot;unterminated</p>\n` with `[foo]` registered as an LRD — cmark + markdown-it-py agree
- **Actual:** `<p>[foo]: /url\n&quot;unterminated</p>\n` (the entire LRD is discarded)

## Spec
Link reference definitions: when the title is invalid/unterminated, the definition is still valid as destination-only and the title-position text falls through to the next block (spec example 70).

Root cause: marko inline_parser `_parse_link_dest_title` raises on the unterminated title and `LinkRefDef.match` returns False for the whole LRD instead of falling back to destination-only.


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
