# [marko] Lone list marker at end of input is rendered as a paragraph

**Target:** frostming/marko · **Version:** 2.2.3 · **Python:** 3.11
**Severity:** medium — incorrect output vs CommonMark 0.31.2.

## Summary

A bullet or ordered list marker that is the final character of the input (no
trailing newline) is rendered as a paragraph instead of an empty list item.

```python
import marko
marko.convert("*")    # -> '<p>*</p>\n'      expected '<ul>\n<li></li>\n</ul>\n'
marko.convert("-")    # -> '<p>-</p>\n'      expected '<ul>\n<li></li>\n</ul>\n'
marko.convert("1.")   # -> '<p>1.</p>\n'     expected '<ol>\n<li></li>\n</ol>\n'
```

With a trailing newline the output is correct (`marko.convert("*\n")` →
`<ul>\n<li></li>\n</ul>\n`), so this is an end-of-input edge case.

## Expected

`<ul>\n<li></li>\n</ul>\n` (and `<ol>…` for `1.`). CommonMark permits empty list
items; `cmark` 0.31.2, `markdown-it-py` 4.2.0, and `mistletoe` 1.5.1 all produce
the empty list. Per the spec, a line may be terminated "by the end of file"
(Preliminaries / "Lines"), so `*` and `*\n` must parse identically.

## Notes

This looks related to marko's documented family of missing-trailing-newline
edge cases (CHANGELOG v2.1.4: "Correct the parsing of LinkRefDef if it is the
last line but doesn't end with a line break"; v2.2.3: "Fix an infinite loop
caused by unnormalized line breaks").

## Duplicate check

No matching issue found via web search of frostming/marko. Please confirm
against the tracker.
