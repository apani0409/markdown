# [mistletoe] Setext heading not recognized inside a block quote

**Target(s):** miyuchina/mistletoe 1.5.1 · **Python:** 3.11

## Reproducer
```python
import mistletoe
print(mistletoe.markdown(">r\n>="))
```

- **Expected:** `<blockquote>\n<h1>r</h1>\n</blockquote>\n` — cmark + markdown-it-py + marko agree
- **Actual:** `<blockquote>\n<p>r\n=</p>\n</blockquote>\n` (treated as a paragraph)

## Spec
Setext headings: a paragraph followed by a `=`/`-` underline becomes a heading; this holds inside container blocks such as block quotes.

Reproduces with `=` (h1) and `-` (h2).


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
