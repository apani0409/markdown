# [mistletoe & marko] Trailing tab-bearing blank line leaks into an indented code block

**Target(s):** miyuchina/mistletoe 1.5.1 · frostming/marko 2.2.3 · **Python:** 3.11

## Reproducer
```python
import mistletoe, marko
print(mistletoe.markdown("\t]\n\t "))
print(marko.convert("\t]\n\t "))
```

- **Expected:** `<pre><code>]\n</code></pre>\n` (trailing blank line dropped) — cmark + markdown-it-py agree
- **Actual:** the trailing tab/space line is kept inside the code block

## Spec
Indented code blocks: blank lines following the block are not included; a line of only spaces/tabs is blank.

The all-spaces equivalent is handled correctly by all four — the defect is treating a *tab*-bearing line as blank. File separately on each project.


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
