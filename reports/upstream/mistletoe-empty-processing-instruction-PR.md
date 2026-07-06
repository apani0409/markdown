# PR (ready to submit): mistletoe — empty inline processing instruction `<??>`

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0011-Fix-an-empty-inline-processing-instruction-is-valid-.patch`](patches/mistletoe/)

> One-character change in `span_token.py` (+ a test). `git am` the patch.

## Suggested PR title

> Fix: an empty inline processing instruction (`<??>`) is valid raw HTML

## Suggested PR body

**What**

```python
import mistletoe
mistletoe.markdown("a<??>b")   # was '<p>a&lt;??&gt;b</p>';  cmark: '<p>a<??>b</p>'
```

**Spec** — a [processing instruction](https://spec.commonmark.org/0.31.2/#processing-instruction)
is `<?`, *"a string of characters not including the string `?>`"*, and `?>`. That
string may be **empty**, so `<??>` is a valid (empty) processing instruction.

**Root cause** — the inline pattern is `r'(?<!\\)<\?.+?\?>'`; `.+?` requires at
least one character, so `<??>` doesn't match and is escaped as text.

```diff
-_instruction = r'(?<!\\)<\?.+?\?>'
+_instruction = r'(?<!\\)<\?.*?\?>'
```

**Verification** — matches cmark on a processing-instruction matrix; an isolated
before/after diff over spec.txt + 12,000 PI-shaped fuzz inputs is **strictly
improving — 1,228 inputs move to cmark's output, 0 regressions**. Full suite:
**351 passed, 1 skipped**. Adds a test.

**Found by** differential testing vs the CommonMark spec + cmark reference.
