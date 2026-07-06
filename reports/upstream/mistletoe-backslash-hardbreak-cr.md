# [mistletoe] Backslash hard line break not recognized before a CR line ending

**Target(s):** miyuchina/mistletoe 1.5.1 · **Python:** 3.11

## Reproducer
```python
import mistletoe
print(mistletoe.markdown("\\\r x"))   # backslash, CR, then text
```

- **Expected:** `<p><br />\n…</p>` — cmark + markdown-it-py + marko agree
- **Actual:** `<p>\\\r\n…</p>` (literal backslash; no hard break)

## Spec
Hard line breaks: a backslash before a line ending is a hard break. mistletoe handles `\n` but not a `\r`/CRLF line ending here.

A line-ending-normalization gap (CR vs LF).


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
