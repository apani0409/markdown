# [marko] `<!` (without a following ASCII letter) wrongly starts an HTML block

**Target:** frostming/marko · **Version:** 2.2.3 · **Python:** 3.11
**Severity:** medium — incorrect output vs CommonMark 0.31.2; raw passthrough of
text that should be escaped.

## Summary

A line beginning with `<!` that is **not** followed by an ASCII letter is treated
by marko as an HTML declaration block and emitted raw, instead of being escaped
as paragraph text.

```python
import marko
marko.convert("<!")    # -> '<!'                  expected '<p>&lt;!</p>\n'
marko.convert("<!>")   # -> '<!>'                 expected '<p>&lt;!&gt;</p>\n'
marko.convert("<! ")   # -> '<! '                 expected '<p>&lt;!</p>\n'
marko.convert("<!-")   # -> '<!-'                 expected '<p>&lt;!-</p>\n'
marko.convert("<!x")   # -> '<!x\n'   (correct — valid type-4 declaration)
```

cmark 0.31.2, markdown-it-py 4.2.0, and mistletoe 1.5.1 all produce
`<p>&lt;!</p>` for `<!`.

## Spec

CommonMark *HTML blocks*, start condition type 4: "line begins with the string
`<!` **followed by an ASCII letter**." (Comments are type 2 — `<!--`; CDATA is
type 5 — `<![CDATA[`.) `<!` alone matches no start condition, so it is a
paragraph; `<` is escaped to `&lt;`.

## Root cause

`marko/block.py` (HTMLBlock match), the type-4 declaration check:

```python
if source.expect_re(r" {,3}<!"):        # line 303 in 2.2.3
```

omits the mandatory ASCII-letter guard. Suggested fix:

```python
if source.expect_re(r" {,3}<![A-Za-z]"):
```

(This also tightens the precedence with the `<![CDATA[` type-5 check that
follows it.)

## Status

A ready-to-submit patch + PR text is prepared:
[`marko-bang-html-block-PR.md`](marko-bang-html-block-PR.md) and
[`patches/`](patches/). Verified against marko 2.2.3: fix works, **1401 tests
pass** (no regressions), and it also fixes the dead `<![CDATA[` branch.

## Duplicate check

No matching issue found via web search of frostming/marko (note: an existing
issue, "HTMLBlock pattern matching does not match CommonMark spec" #61, concerns
HTML blocks generally — please check whether it overlaps before filing).
