# [marko] Interior blank line in an indented code block inside a block quote loses residual indentation

**Target(s):** frostming/marko 2.2.3 · **Python:** 3.11

## Reproducer
```python
import marko
print(marko.convert(">>>     1\n>>>      \n>>>     >"))
```

- **Expected:** interior blank line keeps its residual space: `<pre><code>1\n \n&gt;\n</code></pre>` — cmark + markdown-it-py + mistletoe agree
- **Actual:** `<pre><code>1\n\n&gt;\n</code></pre>` (residual space dropped)

## Spec
Indented code blocks: "Any initial spaces or tabs beyond four spaces of indentation will be included in the content, even in interior blank lines."

Only triggers inside a block quote; the bare indented-code example is fine in marko.


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
