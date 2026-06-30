# PR (ready to submit): mistletoe — autolink URI accepts control chars (tab/newline)

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/mistletoe/0006-Fix-autolink-URI-must-reject-ASCII-control-character.patch`](patches/mistletoe/)

> Independent of the other fixes (touches only `span_token.py` /
> `test_span_token.py`). `git am` the patch.

## Suggested PR title

> Fix: autolink URI must reject ASCII control characters and space

## Suggested PR body

**What** — A tab, newline, or other ASCII control character inside an autolink
URI wrongly forms a link:

```python
import mistletoe
mistletoe.markdown("<hs:\t>")
# was: <p><a href="hs:%09">hs:\t</a></p>
# cmark / markdown-it-py / marko: <p>&lt;hs:\t&gt;</p>   (not an autolink)
```

**Spec** — A CommonMark *absolute-URI* autolink is a scheme, then `:`, then
"any character other than ASCII control characters, space, `<`, and `>`"
(<https://spec.commonmark.org/0.31.2/#autolinks>).

**Root cause** — the URI character class was `[^ <>]`, which only excludes space,
`<` and `>` — not control characters (tab `\t` = 0x09, newline `\n` = 0x0A, …):

```diff
-    pattern = re.compile(r"...<([A-Za-z][A-Za-z0-9+.-]{1,31}:[^ <>]*?|...)>")
+    pattern = re.compile(r"...<([A-Za-z][A-Za-z0-9+.-]{1,31}:[^\x00-\x20<>]*?|...)>")
```

`[^\x00-\x20<>]` excludes 0x00–0x20 (all C0 controls **and** space) plus `<`/`>`,
matching cmark's `[^\x00-\x20<>]` exactly — including that 0x7F (DEL) is still
allowed (cmark allows it too). The new class is a **strict subset** of the old
one, so it can only stop forming the buggy control-char autolinks; it can never
break a valid autolink.

**Verification** — patched parser agrees with cmark across control characters; an
isolated original-vs-patched differential over spec.txt (652) + 10,000
autolink-shaped inputs shows **every** diff is "control-char autolink correctly
rejected" and **0** other changes. Full suite: **343 passed, 1 skipped**.

**Tests** — added a regression test (`tab`, `\n`, `\x01`, space rejected; a
control-free URI still parses).

**Found by** differential testing vs the CommonMark spec + cmark reference.
