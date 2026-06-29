# [markdown-it-py & marko] Unclosed fenced code block at EOF drops the final newline

**Targets:** executablebooks/markdown-it-py 4.2.0 · frostming/marko 2.2.3
**Python:** 3.11 · **Severity:** low/medium — incorrect output vs CommonMark 0.31.2.

## Summary

When a fenced code block is left open (no closing fence) and its last content
line is not terminated by a newline, both parsers drop the trailing newline from
the code content.

```python
from markdown_it import MarkdownIt
import marko
MarkdownIt("commonmark").render("~~~\nt")  # -> '<pre><code>t</code></pre>\n'
marko.convert("~~~\nt")                     # -> '<pre><code>t</code></pre>\n'
# expected (cmark 0.31.2, mistletoe 1.5.1): '<pre><code>t\n</code></pre>\n'
```

## Expected

`<pre><code>t\n</code></pre>\n`. Each content line of a code block renders with a
trailing newline. The CommonMark spec defines a line as ending with a line
ending **or the end of file** (Preliminaries / "Lines"), so the final line `t`
must be treated like `t\n`.

## Evidence it is an EOF edge case (not a config difference)

- `~~~\nt\n` (trailing newline): all four parsers agree on `…t\n…`.
- `~~~\nt\n~~~` (closed fence): both emit `t\n`.
- `    code` (indented code at EOF): both emit `code\n` correctly.

Only the *unclosed fence whose last line lacks a newline* drops it
(reproducible with `~~~\nt\nu` → trailing `u` also loses its newline).

## Duplicate check

No matching issue found via web search. Please confirm against each tracker.
File separately on markdown-it-py and marko (independent codebases).
