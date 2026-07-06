# PR (ready to submit): markdown-it-py — image `alt` drops entities/escapes/code/hard-breaks

**Repo:** executablebooks/markdown-it-py · **Base:** v4.2.0 · **Patch:**
[`patches/markdown-it-py/0001-Fix-image-alt-text-drops-entities-escapes-code-spans.patch`](patches/markdown-it-py/)

> Touches only `markdown_it/renderer.py` (+ a new test). `git am` the patch.

## Suggested PR title

> Fix: image `alt` text drops entities, backslash escapes, code spans and hard breaks

## Suggested PR body

**What** — Inline content inside an image description is lost from the rendered
`alt` attribute:

```python
from markdown_it import MarkdownIt
md = MarkdownIt("commonmark")
md.render("![x&#65;y](/u)")   # alt="xy"   -> the entity 'A' is dropped
md.render(r"![\!](/u)")       # alt=""      -> backslash escape dropped
md.render("![`c`](/u)")       # alt=""      -> code-span text dropped
md.render("![a  \nb](/u)")    # alt="ab"    -> hard break dropped, words glued
```

cmark 0.31.2 renders these as `alt="xAy"`, `alt="!"`, `alt="c"`, `alt="a b"`.

**Spec** — an image description contains inline content and *"entity and numeric
character references are parsed"*
([§6.5](https://spec.commonmark.org/0.31.2/#images)); the `alt` shows that
content with markup stripped, so the text must survive.

**Root cause** — `renderInlineAsText` only emits `text`, nested `image`, and
`softbreak` tokens. Entities and backslash escapes are `text_special` tokens; the
core `text_join` rule that folds them into `text` runs over top-level inline
tokens, not over an image's *nested* `alt` children, so they reach
`renderInlineAsText` intact — and are dropped, together with `code_inline`,
`html_inline` and `hardbreak`.

**Fix**

```diff
 for token in tokens or []:
-    if token.type == "text":
+    if token.type in ("text", "text_special", "code_inline", "html_inline"):
         result += token.content
     elif token.type == "image":
         if token.children:
             result += self.renderInlineAsText(token.children, options, env)
-    elif token.type == "softbreak":
+    elif token.type in ("softbreak", "hardbreak"):
         result += "\n"
```

**Verification** — patched `alt` matches cmark on entities, hex/named references,
backslash escapes, code spans and raw inline HTML. An isolated before/after diff
over the CommonMark spec.txt (652) + 15,000 image-shaped fuzz inputs changes
**only** `<img>` `alt` text (0 other changes); `renderInlineAsText` is used
solely for `alt`, so nothing else can be affected. spec.txt conformance is
unchanged (652/652). Adds parameterised tests (8/10 fail on the unpatched base).

**Note** — the token model matches upstream markdown-it (JS); it likely has the
same gap and this may be worth cross-filing there.

**Found by** differential testing vs the CommonMark spec + cmark reference.
