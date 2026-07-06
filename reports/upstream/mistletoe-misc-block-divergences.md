# [mistletoe] Two further block-level divergences (root-caused, not yet patched)

**Target:** miyuchina/mistletoe 1.5.1 · found by the differential hunt vs cmark
0.31.2. Reported with root cause; a clean fix is deeper than the one-liners
already shipped, so they are left for maintainer judgement.

## 1. A whitespace-only (tab) line becomes an indented code block

```python
import mistletoe
mistletoe.markdown("\t")     # '<pre><code>\t\n</code></pre>';  cmark: '' (blank)
mistletoe.markdown("\t x")   # (tab then text) is a real code block -- unaffected
```

A line consisting only of whitespace is a [blank line](https://spec.commonmark.org/0.31.2/#blank-line)
and cannot open (or sit inside) an indented code block. mistletoe's indented-code
/ blank-line detection treats a leading tab (≥4 columns) as code even when the
rest of the line is empty. Fix direction: a line that is *only* whitespace must
be classified blank before the 4-column indented-code test.
*(Also: `\x0b`/`\x0c` vertical-tab / form-feed lines differ from cmark, a related
whitespace-classification gap.)*

## 2. A literal backslash before a code span is dropped

```python
import mistletoe
mistletoe.markdown(r"\\`x`")   # '<p><code>x</code></p>';  cmark: '<p>\<code>x</code></p>'
```

`\\` is an escaped backslash (one literal `\`), then a code span. mistletoe drops
the literal `\`. Root cause: the code-span pattern
`r"(?<!\\|`)(?:\\\\)*(`+)(?!`)(.+?)(?<!`)\1(?!`)"` matches the leading `\\` via
`(?:\\\\)*` and folds it into the code-span match span, so it is consumed and
lost when the span is replaced. The `(?:\\\\)*` is there to let an *escaped*
backslash precede an opening backtick, but it should not be absorbed into the
emitted code span. Fix direction: exclude the leading backslash run from the code
span's start offset (e.g. a look-behind, or emit it as preceding text). This is
delicate core code-span matching, so it is reported rather than patched blind.

## How it was found

Feature-area finders (`backslash`, `indented`) running ~7k inputs vs the cmark
reference. Data: `findings/` (hunt) + `reports/performance.md` methodology.
