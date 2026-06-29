# Upstream contribution drafts (M3)

Ready-to-file drafts for the genuine findings (see [`../findings-m2.md`](../findings-m2.md)
for the full triaged list). All are **correctness/robustness** bugs — none are
secret vulnerabilities, so they can be filed publicly. Actual filing requires
write access / a maintainer contact and is intentionally left to a human (the
session that produced these had read-only, single-repo GitHub scope).

| Draft | Target(s) | Finding | Severity |
|---|---|---|---|
| [mistletoe-crash-emphasis.md](mistletoe-crash-emphasis.md) | mistletoe | `IndexError` crash on emphasis runs | high |
| [marko-bang-html-block.md](marko-bang-html-block.md) | marko | `<!` (no ASCII letter) wrongly starts an HTML block — one-line fix | medium |
| [marko-lone-list-marker-eof.md](marko-lone-list-marker-eof.md) | marko | lone list marker at EOF → paragraph | medium |
| [unclosed-fence-eof-newline.md](unclosed-fence-eof-newline.md) | markdown-it-py, marko | unclosed fence at EOF drops final newline | low/med |
| [tab-partial-consume-blockquote.md](tab-partial-consume-blockquote.md) | markdown-it-py, mistletoe | partial tab after block-quote marker drops a space | medium |
| [mistletoe-image-alt-softbreak.md](mistletoe-image-alt-softbreak.md) | mistletoe | soft break dropped in image `alt` | medium |
| [commonmark-spec-test-proposals.md](commonmark-spec-test-proposals.md) | commonmark-spec | two under-specified LRD edge cases | spec |

The full adversarially-verified catalog (25 confirmed bugs) is in
[`../findings-verified.md`](../findings-verified.md). Findings with evidence but
no standalone draft yet (ready to expand from the catalog): marko
unterminated-LRD-title fallback and block-quote indented-code blank line;
markdown-it-py lazy-continuation-after-LRD; mistletoe bare-`)` list marker; and
several emphasis/code-span and list edge cases.

[`reproduce.py`](reproduce.py) demonstrates the key cases with only the
third-party parsers installed (no cm-difftest dependency).

## Before filing (checklist per draft)
1. Re-run `reproduce.py` against the exact pinned versions.
2. Search the target's issue tracker for duplicates (web search done; confirm).
3. For shared findings, file independently on each affected project.
4. Keep titles/repros minimal; link to the spec section cited in the draft.
