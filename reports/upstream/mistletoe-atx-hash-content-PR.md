# PR (ready to submit): mistletoe — ATX heading over-strips a `#`-only content run

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0010-Fix-ATX-heading-over-strips-a-only-content-run.patch`](patches/mistletoe/)

> Touches only `block_token.py` / `test_block_token.py`. `git am` the patch.

## Suggested PR title

> Fix: ATX heading over-strips a `#`-only content run

## Suggested PR body

**What** — heading text made only of `#` characters is dropped:

```python
import mistletoe
mistletoe.markdown("# # #")     # was '<h1></h1>';   cmark: '<h1>#</h1>'
mistletoe.markdown("#  ##  #")  # was '<h1></h1>';   cmark: '<h1>##</h1>'
```

**Spec** — in an [ATX heading](https://spec.commonmark.org/0.31.2/#atx-headings)
the closing sequence is a trailing run of `#` preceded by spaces or tabs; content
before it is kept. In `# # #` the *last* `#` is the closing sequence and the
middle `#` is content.

**Root cause** — `Heading.start` cleared the content whenever it was all `#`
(`set(content) == {'#'}`), to make `# #` an empty heading — but that also dropped
legitimate `#` content:

```python
cls.content = (match_obj.group(2) or '').strip()
if set(cls.content) == {'#'}:
    cls.content = ''
```

A `#` run is the closing sequence only when *no separate* `#` closing run was
matched into group 3 (`# #` → group 3 is just the newline; `# # #` → group 3 is
` #`). Guard on that:

```diff
-        if set(cls.content) == {'#'}:
+        if set(cls.content) == {'#'} and '#' not in (match_obj.group(3) or ''):
             cls.content = ''
```

**Verification** — matches cmark on the ATX closing-sequence matrix; an isolated
before/after diff over the CommonMark spec.txt + 15,000 ATX-shaped fuzz inputs is
**strictly improving — 638 inputs move to cmark's output, 0 regressions**. Full
suite: **351 passed, 1 skipped**. Adds a test.

**Found by** differential testing vs the CommonMark spec + cmark reference.
