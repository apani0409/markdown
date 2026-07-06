# PR (ready to submit): marko — O(n²) on `[](`×n (cap link-dest paren nesting)

**Repo:** frostming/marko · **Base:** v2.2.3 · **Patch:**
[`patches/marko/0003-Fix-cap-link-destination-paren-nesting-at-32-matches.patch`](patches/marko/)

> Independent of the `<!` and lone-list-marker fixes (touches only
> `inline_parser.py` / `tests/test_basic.py`), so it can be filed as its own PR
> or applied alongside. `git am` the patch.

## Suggested PR title

> Fix: cap link-destination paren nesting at 32 (matches cmark; fixes O(n²) on `[](`×n)

## Suggested PR body

**What** — `[](`×n is quadratic, *and* destinations nested >32 parens deep are
mis-parsed as links.

```python
import marko, time
for n in (1000, 2000, 4000, 8000):
    s = "[](" * n
    t = time.perf_counter(); marko.convert(s)
    print(3 * n, round(time.perf_counter() - t, 4))
# before:  exponent ≈ 1.99 (O(n²));  after: exponent ≈ 0.93 (linear)

# conformance: a destination nested 33 deep
md = "[a](" + "(" * 33 + "x" + ")" * 33 + ")"
# cmark 0.31.2: literal text (not a link);  marko before: <a href=…> (wrong)
```

**Root cause** — `_parse_link_dest_title` scans a bare (non-`<>`) destination
counting nested `(`/`)` with **no depth limit**. For `[](`×n (a run of unbalanced
`(` with no closing `)`) the `pairs` counter never returns to zero and there is
no whitespace, so every `]` scans to end-of-input → **O(n²)** (profiling
`'[]('*2000`: `_parse_link_dest_title` = 80% of runtime, 6M `len()` calls).

**Fix** — adopt the same cap as CommonMark's reference parser (`cmark`'s
`manual_scan_link_url_2`: `if (nb_p > 32) return -1;`). marko's `pairs` counter
matches cmark's `nb_p` exactly:

```diff
             elif c == "(":
                 pairs += 1
+                if pairs > 32:
+                    raise ParseError("Link destination nesting too deep")
             elif c == ")":
                 if pairs > 0:
                     pairs -= 1
```

This bounds the scan to ~32 characters per `]` (→ linear) **and** makes marko
agree with cmark on deep nesting.

**Verification** — patched marko agrees with cmark at destination paren depths
**1…100** (boundary exactly at 32/33); **0 output diffs** vs original across
spec.txt (652) and 12k bracket-heavy fuzz inputs (which never nest >32 deep);
`[](`×n drops from exp ≈1.99 to ≈0.93. Full suite: **1412 passed**.

**Tests** — added a 32/33-boundary conformance test and a linear-scaling test
for `[](`×n.

**Scope** — `[`×n`]`×n is still quadratic from an independent source
(`look_for_image_or_link` → `is_paired` re-scans the growing link text on every
`]`); there is no spec cap analogous to the paren limit, so it is a deeper change
left for separate work.

**Found by** differential algorithmic-complexity measurement vs the cmark
reference.
