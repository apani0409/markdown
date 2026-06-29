# PR (ready to submit): marko — `<!` HTML-block fix

**Repo:** frostming/marko · **Base:** v2.2.3 · **Patch:**
[`patches/0001-Fix-without-an-ASCII-letter-must-not-start-an-HTML-b.patch`](patches/)

Apply with:

```bash
git clone https://github.com/frostming/marko && cd marko
git am < 0001-Fix-without-an-ASCII-letter-must-not-start-an-HTML-b.patch
# or: git apply --index <patch>
pytest tests/        # 1401 passed
```

## Suggested PR title

> Fix: `<!` without an ASCII letter must not start an HTML block (+ fix dead CDATA branch)

## Suggested PR body

**What**

`marko.block.HTMLBlock.match` matched a bare `<!` as an HTML *declaration* block
(start condition 4). Per CommonMark, condition 4 requires `<!` **followed by an
ASCII letter**. As a result:

```python
import marko
marko.convert("<!")    # was: '<!'            now: '<p>&lt;!</p>\n'
marko.convert("<!>")   # was: '<!>'           now: '<p>&lt;!&gt;</p>\n'
marko.convert("<!-")   # was: '<!-'           now: '<p>&lt;!-</p>\n'
```

cmark 0.31.2, markdown-it-py, and mistletoe all produce the paragraph form.

The same condition-4 check also preceded the `<![CDATA[` (condition 5) check, so
condition 5 was effectively dead and CDATA sections were parsed as declarations
(ending at the first `>` instead of `]]>`). Fixed by testing condition 5 first
and requiring an ASCII letter for condition 4.

**Change** — `marko/block.py` (2 lines moved, 1 regex tightened):

```diff
-        if source.expect_re(r" {,3}<!"):
-            source.context.html_end = re.compile(r">")
-            return 4
         if source.expect_re(r" {,3}<!\[CDATA\["):
             source.context.html_end = re.compile(r"\]\]>")
             return 5
+        if source.expect_re(r" {,3}<![A-Za-z]"):
+            source.context.html_end = re.compile(r">")
+            return 4
```

**Tests** — added to `tests/test_basic.py`; the full suite passes (**1401
passed**), no regressions (incl. `tests/test_spec.py` CommonMark conformance).

**Found by** differential testing against the CommonMark spec + the cmark
reference. Happy to adjust the changelog/wording as you prefer.
