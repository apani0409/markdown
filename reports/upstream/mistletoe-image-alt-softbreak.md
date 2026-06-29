# [mistletoe] Soft line break inside image `alt` text is dropped (words glued together)

**Target:** miyuchina/mistletoe · **Version:** 1.5.1 · **Python:** 3.11
**Severity:** medium — incorrect/garbled `alt` text vs CommonMark 0.31.2.

## Summary

A soft line break inside an image description is deleted entirely from the `alt`
attribute, concatenating the surrounding words with no separator.

```python
import mistletoe
mistletoe.markdown("![a\nb]()")     # -> '<p><img src="" alt="ab" /></p>\n'
mistletoe.markdown("![x\ny\nz]()")  # -> alt="xyz"
mistletoe.markdown("![\n]()")       # -> alt=""
```

## Expected

The CommonMark *Soft line breaks* rule: "A conforming parser may render a soft
line break in HTML either as a line ending **or as a space**." There is no third
option — dropping it is non-conformant. cmark 0.31.2 renders it as a space
(`alt=" "`, `alt="a b"`); markdown-it-py and marko render it as a line ending
(`alt="\n"`, `alt="a\nb"`). Both are valid; mistletoe's deletion is not.

mistletoe renders soft breaks correctly in normal paragraph text — the defect is
isolated to its plain-text/`alt` rendering path.

## Duplicate check

No matching issue found via web search of miyuchina/mistletoe. Please confirm
against the tracker.
