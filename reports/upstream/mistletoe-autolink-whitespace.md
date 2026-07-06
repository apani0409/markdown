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

> **Status: verified fix** — [`mistletoe-autolink-whitespace-PR.md`](mistletoe-autolink-whitespace-PR.md)
> / [`patches/mistletoe/0006-*.patch`](patches/mistletoe/). The URI class `[^ <>]`
> only excluded space; changed to `[^\x00-\x20<>]` (exclude all C0 controls +
> space, like cmark). Strict subset of the old class → can only reject the buggy
> control-char autolinks. Isolated diff over spec.txt + 10k autolink inputs: every
> diff is "control-char autolink correctly rejected", 0 other changes; 343 tests pass.


## Duplicate check
No matching issue found via web search; please confirm against the tracker before filing.
