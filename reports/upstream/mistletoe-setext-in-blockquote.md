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

## Root cause (analysed — deeper fix, not a clean one-liner)

`Quote.read` (`block_token.py`) tokenizes the quote's inner lines with
`Paragraph.parse_setext = False`, i.e. it **disables setext headings entirely
inside block quotes**. That is an over-broad workaround for a real spec rule:

> A setext heading underline **cannot be a lazy continuation line** in a list
> item or block quote.

So the two cases must be distinguished (confirmed vs cmark 0.31.2):

| Input | cmark | mistletoe |
|---|---|---|
| `>r`⏎`>=` (underline has its own `>`) | `<h1>r</h1>` | `<p>r\n=</p>` ✗ |
| `>r`⏎`=` (lazy underline, no `>`)     | `<p>r\n=</p>` | `<p>r\n=</p>` ✓ |

mistletoe gets the *lazy* case right (by disabling setext) but the *non-lazy*
case wrong. A correct fix has to allow setext only for underlines that carry the
block-quote marker — but by the time `Quote.read` builds `line_buffer`, the
`>`-prefixed lines and the lazy continuation lines have been flattened together
(the marker stripped), so the lazy/non-lazy distinction is lost. Fixing it means
threading that per-line information into setext recognition — a structural change
to the quote/paragraph interaction with genuine regression risk against the lazy
rule. Reported with root cause rather than shipped as a fragile patch.


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
