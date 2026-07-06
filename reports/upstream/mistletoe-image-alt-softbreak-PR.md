# PR (ready to submit): mistletoe — line break in image `alt` dropped / leaks literal chars

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0007-Fix-line-break-in-image-alt-text-dropped-leaks-liter.patch`](patches/mistletoe/)

> Independent of the other fixes (touches only `html_renderer.py` /
> `test_html_renderer.py`). `git am` the patch.

## Suggested PR title

> Fix: line break in image `alt` text dropped / leaks literal characters

## Suggested PR body

**What** — A line break inside an image description produces wrong `alt` text:

```python
import mistletoe
mistletoe.markdown("![a\nb]()")     # alt="ab"   (soft break dropped, words glued)
mistletoe.markdown("![a  \nb]()")   # alt="a  b" (hard break's spaces leak in)
mistletoe.markdown("![a\\\nb]()")   # alt="a\\b" (hard break's backslash leaks in)
```

cmark renders all three as `alt="a b"`.

**Spec** — *Soft line breaks*: "A conforming parser may render a soft line break
… either as a line ending or as a space." Dropping it is non-conformant
(<https://spec.commonmark.org/0.31.2/#soft-line-breaks>).

**Root cause** — `render_to_plain` (used to build the `alt` attribute) returns
`token.content` for a leaf token. But a `LineBreak`'s `content` is only its
*leading* characters — `""` for a soft break, `"  "`/`"\\"` for a hard break —
not the break itself. So a soft break contributes nothing (words glue together)
and a hard break leaks its literal prefix.

**Fix** — render a `LineBreak` as a single space in plain-text context, matching
cmark:

```diff
 def render_to_plain(self, token) -> str:
     if token.children is not None:
         inner = [self.render_to_plain(child) for child in token.children]
         return ''.join(inner)
+    if isinstance(token, span_token.LineBreak):
+        return ' '
     return html.escape(token.content)
```

(The spec also permits a line ending; a single space matches cmark and cleanly
handles soft, hard-space, and backslash breaks alike.)

**Verification** — patched parser agrees with cmark on soft/hard/backslash breaks
and multi-line alts; an isolated original-vs-patched differential over spec.txt
(652) + 12,000 image-shaped inputs changes **only** `<img>` `alt` text and
nothing else. Full suite: **348 passed, 1 skipped**.

**Tests** — added parameterized regression tests for soft/hard/backslash/
multi-line alts.

**Found by** differential testing vs the CommonMark spec + cmark reference.
