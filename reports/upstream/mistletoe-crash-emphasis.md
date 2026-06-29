# [mistletoe] `IndexError: string index out of range` parsing certain emphasis-delimiter runs

**Target:** miyuchina/mistletoe · **Version:** 1.5.1 · **Python:** 3.11
**Severity:** high — a parser of untrusted input should never crash.

## Summary

`mistletoe.markdown()` raises `IndexError: string index out of range` on certain
inputs made of `*`/`"`/`+` runs. Minimal reproducer (22 chars, reduced with
delta-debugging so no single character can be removed):

```python
import mistletoe
mistletoe.markdown('****"************+****')
```

```
Traceback (most recent call last):
  ...
  File ".../mistletoe/core_tokens.py", line 117, in process_emphasis
    bottom = star_bottom if closer.type[0] == '*' else underscore_bottom
                            ~~~~~~~~~~~^^^
IndexError: string index out of range
```

## Root cause

In `core_tokens.process_emphasis`, `closer.type[0]` is indexed unconditionally,
but for one delimiter in this configuration `closer.type` is the empty string,
so `[0]` raises. A guard for an empty `type` (or ensuring delimiters always have
a non-empty `type`) would fix it.

## Expected

No crash. The CommonMark reference `cmark` 0.31.2, `markdown-it-py` 4.2.0, and
`marko` 2.2.3 all render the same input without error, e.g. cmark produces:

```html
<p><strong><strong>&quot;</strong></strong>****<strong><strong>+</strong></strong></p>
```

(The exact emphasis nesting is not the point of this report — only that the
input must not crash the parser.)

## How it was found

Surfaced by an Atheris (libFuzzer) coverage-guided fuzzing run against mistletoe
(~262 000 executions), then minimized. Part of a differential-testing harness
comparing the maintained pure-Python CommonMark parsers.

## Duplicate check

No matching open issue found via web search (mistletoe #96 and #175 touch
emphasis parsing but describe different problems). Please confirm against the
tracker before triaging.
