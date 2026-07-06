# [markdown-it-py & mistletoe] Partially-consumed tab after a block-quote marker drops a leading space

**Targets:** executablebooks/markdown-it-py 4.2.0 · miyuchina/mistletoe 1.5.1
**Python:** 3.11 · **Severity:** medium — incorrect output vs CommonMark 0.31.2.

## Summary

When a tab follows a block-quote marker and is only partially consumed by the
marker's delimiter space, the leftover columns must become literal spaces in the
content. markdown-it-py and mistletoe drop one such space.

```python
from markdown_it import MarkdownIt
import mistletoe
MarkdownIt("commonmark").render(">>  \t<")   # nested bq + tab
mistletoe.markdown(">>  \t<")
# both ->  <blockquote><blockquote><pre><code>&lt;       (no leading space)
# expected (cmark 0.31.2, marko 2.2.3):
#          <blockquote><blockquote><pre><code> &lt;      (one leading space)
```

(Same defect with `>>  \t>` and with a plain content char `>>  \tx`.)

## Expected

```html
<blockquote>
<blockquote>
<pre><code> &lt;
</code></pre>
</blockquote>
</blockquote>
```

## Why it is a tab bug (not interpretation latitude)

The pure-space equivalent `>>      <` (six spaces, no tab) renders **identically
in all four** parsers (with the leading space). Per the *Tabs* section, "in
contexts where spaces help to define block structure, tabs behave as if they
were replaced by spaces with a tab stop of 4 characters", and the partial-
consumption example `>→→foo` → `<pre><code>  foo` shows leftover tab columns
becoming literal content spaces. So the tab form must equal the space form.
markdown-it-py and mistletoe diverge only on the tab path → tab-expansion bug.

## Duplicate check

No matching issue found via web search. File separately on each project.
