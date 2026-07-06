# [markdown-it-py] Image `alt` text drops entities, escapes, code spans and hard breaks

**Target:** executablebooks/markdown-it-py · **Version:** 4.2.0 · **Python:** 3.11
**Severity:** medium — silent loss of `alt` content (accessibility / correctness) vs CommonMark 0.31.2.

Found by the differential hunt (the area finders ran ~44k inputs vs the cmark
reference). Notable because markdown-it-py is **100% on `spec.txt`** in our
scorecard — the spec suite has no example with an entity/escape/code span inside
an image description, so this gap is invisible to it and only differential
fuzzing surfaces it.

## Reproducers

```python
from markdown_it import MarkdownIt
md = MarkdownIt("commonmark")

md.render("![x&#65;y](/u)")   # alt="xy"   (entity 'A' dropped);  cmark: alt="xAy"
md.render("![&amp;](/u)")     # alt=""      (named entity dropped); cmark: alt="&amp;"
md.render(r"![\!](/u)")       # alt=""      (backslash escape dropped); cmark: alt="!"
md.render("![`c`](/u)")       # alt=""      (code-span text dropped); cmark: alt="c"
md.render("![a  \nb](/u)")    # alt="ab"    (hard break dropped -> words glued); cmark: alt="a b"
```

The same entities/escapes render correctly in **paragraph text, link text, and
emphasis** — the defect is isolated to the image-`alt` plain-text path.

## Spec

An image description may contain the usual inline content, and *"entity and
numeric character references are parsed"* (CommonMark
[§6.5 Images](https://spec.commonmark.org/0.31.2/#images)); the rendered `alt`
shows that content with markup stripped. Dropping the entity/escape/code text is
non-conformant. (cmark 0.31.2, mistletoe and marko all keep it.)

## Root cause

`RendererHTML.renderInlineAsText` (which builds the `alt` string) only emits
`text`, nested `image`, and `softbreak` tokens:

```python
for token in tokens or []:
    if token.type == "text":
        result += token.content
    elif token.type == "image":
        if token.children:
            result += self.renderInlineAsText(token.children, options, env)
    elif token.type == "softbreak":
        result += "\n"
```

Entities and backslash escapes are tokenised as **`text_special`**. The core
`text_join` rule that folds `text_special` into `text` runs over *top-level*
inline tokens, but an image's `alt` children are parsed as a *nested* sub-tree
(`image.py`: `state.md.inline.parse(content, …); token.children = tokens`), so
`text_join` never visits them. Their `text_special` tokens therefore reach
`renderInlineAsText` intact and are dropped — as are `code_inline`, `html_inline`
and `hardbreak` tokens.

## Fix

Emit `text_special` / `code_inline` / `html_inline` content and render a hard
break as a newline (soft breaks already are). See
[`patches/markdown-it-py/0001-*.patch`](patches/markdown-it-py/) /
[`markdown-it-py-image-alt-PR.md`](markdown-it-py-image-alt-PR.md).

**Verification:** patched `alt` matches cmark on entities, hex/named refs,
escapes, code spans and raw HTML; an isolated before/after diff over spec.txt +
15,000 image-shaped fuzz inputs changes **only** `<img>` `alt` (0 other changes),
and spec.txt conformance is unchanged (652/652). New tests added (8/10 fail on
the unpatched baseline).

**Upstream note:** the token model is shared with markdown-it (JS), so JS
markdown-it likely has the same gap; worth cross-filing.
