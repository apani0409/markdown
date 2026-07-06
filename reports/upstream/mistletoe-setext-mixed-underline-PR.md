# PR (ready to submit): mistletoe — mixed `=-` accepted as a setext underline

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0009-Fix-a-setext-underline-must-be-all-or-all-not-a-mix.patch`](patches/mistletoe/)

> Touches only `block_token.py` / `test_block_token.py`. `git am` the patch.

## Suggested PR title

> Fix: a setext underline must be all `=` or all `-`, not a mix

## Suggested PR body

**What** — a paragraph followed by a *mixed* run of `=`/`-` is wrongly parsed as a
setext heading:

```python
import mistletoe
mistletoe.markdown("a\n=-")   # was '<h2>a</h2>';   cmark: '<p>a\n=-</p>'
mistletoe.markdown("a\n-=")   # was '<h2>a</h2>';   cmark: '<p>a\n-=</p>'
```

**Spec** — a [setext heading underline](https://spec.commonmark.org/0.31.2/#setext-heading-underline)
is *"a sequence of `=` characters or a sequence of `-` characters"* — a single
character type, not a mix.

**Root cause** — `Paragraph.setext_pattern` is `r' {0,3}(=|-)+ *$'`; the group
`(=|-)+` matches each character independently, so `=-` and `-=` match.

```diff
-    setext_pattern = re.compile(r' {0,3}(=|-)+ *$')
+    setext_pattern = re.compile(r' {0,3}(=+|-+) *$')
```

`(=+|-+)` requires the whole run to be one character type. The heading level is
computed separately (from the underline's first non-space char), so this change
only affects *whether* a line is an underline.

**Verification** — matches cmark on the underline-acceptance matrix; an isolated
before/after diff over the CommonMark spec.txt + 15,000 setext-shaped fuzz inputs
is **strictly improving — 1,111 inputs move to cmark's output, 0 regressions**.
Full suite: **350 passed, 1 skipped**. Adds tests.

**Found by** differential testing vs the CommonMark spec + cmark reference.

---

### Related (not in this PR)

A setext underline with a *trailing tab* (`a\n-⇥`) is also rejected where cmark
accepts it. Fixing that in isolation is correct, but it then exposes a separate
pre-existing bug — mistletoe applies a setext underline as a **lazy continuation
line** inside a block quote / list item, which CommonMark forbids
([`mistletoe-setext-in-blockquote.md`](mistletoe-setext-in-blockquote.md)). The
trailing-tab fix is therefore deferred to that change to avoid net regressions.
