# PR (ready to submit): mistletoe — `IndexError` in `process_emphasis`

**Repo:** miyuchina/mistletoe · **Base:** v1.5.1 · **Patch:**
[`patches/0001-Fix-IndexError-in-process_emphasis-on-certain-emphas.patch`](patches/)

Apply with:

```bash
git clone https://github.com/miyuchina/mistletoe && cd mistletoe
git am < 0001-Fix-IndexError-in-process_emphasis-on-certain-emphas.patch
pip install parameterized pygments && pytest test/   # 335 passed, 1 skipped
```

## Suggested PR title

> Fix: `IndexError` in `process_emphasis` on certain emphasis-delimiter runs

## Suggested PR body

**What** — `mistletoe.markdown()` raises `IndexError: string index out of range`
on a class of inputs made of `*` runs separated by single characters. Minimal
case (9 chars):

```python
import mistletoe
mistletoe.markdown('**"****_*')   # IndexError
```

It is a class, not a one-off — e.g. `**+****+*`, `` **`****~* ``, `**~****"*`
(100+ minimal variants of the shape `**<sep>****<sep>*`). The reference cmark,
markdown-it-py, and marko all render these without error.

**Root cause** — `Delimiter.remove(n, left=False)` in `core_tokens.py`:

```diff
         self.end = self.end - n
         self.number = self.end - self.start
-        self.type = self.type[:n]
+        self.type = self.type[:-n]
         return True
```

When removing `n` delimiter characters from the **right**, the remaining run is
the *left* part (`type[:-n]`), but the code kept the *first* `n` characters
(`type[:n]`). That desynchronizes `type` from `number`; after further removals
`type` can become `''` while `number > 0`, so the next iteration of
`process_emphasis` crashes at `closer.type[0]`.

(The existing `test_delimiter_remove_right` didn't catch it because it removes
`n=1` from a 2-char run, where `type[:1] == type[:-1]` coincidentally.)

**Tests** — added a `Delimiter.remove(left=False)` unit test that asserts
`type`/`number` stay in sync, plus an integration test on the minimal crashers.
Full suite: **335 passed, 1 skipped**, no regressions (incl. CommonMark spec).

**Scope (honest note).** This patch fixes the **crash** (the critical issue) and
passes the full suite. It does *not* claim to make emphasis parsing on these
contrived runs match the reference: with the crash gone, e.g. `**"****_*` now
renders as `<strong>"</strong>*<em>_</em>`, whereas cmark and markdown-it produce
`**&quot;***<em>_</em>`. That residual emphasis divergence is a separate,
lower-severity correctness matter (no spec example covers it; all 335 tests pass)
— happy to open a follow-up issue if you'd like, but it's out of scope for this
crash fix. A 600 000-input structure-aware re-fuzz of the patched build found
**no remaining crashes**.

**Found by** Atheris coverage-guided fuzzing + delta-debugging in a differential
harness across the maintained Python CommonMark parsers. Glad to tweak as needed.
