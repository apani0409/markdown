# [mistletoe] Autolink wrongly accepts whitespace (tab) in the URI

**Target(s):** miyuchina/mistletoe 1.5.1 · **Python:** 3.11

## Reproducer
```python
import mistletoe
print(mistletoe.markdown("<hs:\t>"))
```

- **Expected:** `<p>&lt;hs:\t&gt;</p>\n` — cmark + markdown-it-py + marko agree (not an autolink)
- **Actual:** `<p><a href="hs:%09">hs:\t</a></p>\n` (forms a link)

## Spec
Autolinks: an absolute URI autolink may not contain whitespace (`<` ... `>` with no spaces/tabs).


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
