# Upstream contribution drafts (M3)

Ready-to-file drafts for the genuine findings (see [`../findings-m2.md`](../findings-m2.md)
for the full triaged list). All are **correctness/robustness** bugs — none are
secret vulnerabilities, so they can be filed publicly. Actual filing requires
write access / a maintainer contact and is intentionally left to a human (the
session that produced these had read-only, single-repo GitHub scope).

| Draft | Target(s) | Finding | Severity |
|---|---|---|---|
| [mistletoe-crash-emphasis.md](mistletoe-crash-emphasis.md) · **[PR](mistletoe-crash-PR.md)** ✅ | mistletoe | `IndexError` crash on emphasis runs — **verified 1-char fix, 335 tests pass** | high |
| [marko-bang-html-block.md](marko-bang-html-block.md) · **[PR](marko-bang-html-block-PR.md)** ✅ | marko | `<!` (no ASCII letter) wrongly starts an HTML block — **verified fix, 1401 tests pass** | medium |
| [marko-lone-list-marker-eof.md](marko-lone-list-marker-eof.md) · **[PR](marko-lone-list-marker-PR.md)** ✅ | marko | lone list marker at EOF → paragraph — **verified fix, 1408 tests pass** | medium |
| [unclosed-fence-eof-newline.md](unclosed-fence-eof-newline.md) | markdown-it-py, marko | unclosed fence at EOF drops final newline | low/med |
| [tab-partial-consume-blockquote.md](tab-partial-consume-blockquote.md) | markdown-it-py, mistletoe | partial tab after block-quote marker drops a space | medium |
| [mistletoe-image-alt-softbreak.md](mistletoe-image-alt-softbreak.md) | mistletoe | soft break dropped in image `alt` | medium |
| [mistletoe-list-marker-overrecognition.md](mistletoe-list-marker-overrecognition.md) | mistletoe | `.`/`)` wrongly parsed as an empty list | medium |
| [mistletoe-setext-in-blockquote.md](mistletoe-setext-in-blockquote.md) | mistletoe | setext heading missed inside a block quote | medium |
| [mistletoe-autolink-whitespace.md](mistletoe-autolink-whitespace.md) | mistletoe | autolink accepts whitespace (tab) | medium |
| [mistletoe-backslash-hardbreak-cr.md](mistletoe-backslash-hardbreak-cr.md) | mistletoe | backslash hard break missed before CR | low |
| [markdown-it-py-lazy-continuation-after-lrd.md](markdown-it-py-lazy-continuation-after-lrd.md) | markdown-it-py, marko | lazy continuation after LRD in block quote | medium |
| [marko-lrd-unterminated-title.md](marko-lrd-unterminated-title.md) | marko | unterminated title discards whole LRD | medium |
| [marko-blockquote-indented-code-blank-line.md](marko-blockquote-indented-code-blank-line.md) | marko | interior blank line loses residual indent | low/med |
| [shared-trailing-tab-indented-code.md](shared-trailing-tab-indented-code.md) | mistletoe, marko | trailing tab line leaks into indented code | low/med |
| [commonmark-spec-test-proposals.md](commonmark-spec-test-proposals.md) | commonmark-spec | two under-specified LRD edge cases | spec |

These cover every distinct **root-cause class** in the adversarially-verified
catalog ([`../findings-verified.md`](../findings-verified.md),
[`../findings-mistletoe.md`](../findings-mistletoe.md)) — the catalog's 25
confirmed bugs collapse to these classes (many entries are instances of the same
cause, e.g. several lone-marker or emphasis-run variants). A couple of low-value
cosmetic deviations (e.g. mistletoe rendering a literal `"` instead of `&quot;`)
are left in the catalog rather than drafted.

[`reproduce.py`](reproduce.py) demonstrates the key cases with only the
third-party parsers installed (no cm-difftest dependency).

## Before filing (checklist per draft)
1. Re-run `reproduce.py` against the exact pinned versions.
2. Search the target's issue tracker for duplicates (web search done; confirm).
3. For shared findings, file independently on each affected project.
4. Keep titles/repros minimal; link to the spec section cited in the draft.
