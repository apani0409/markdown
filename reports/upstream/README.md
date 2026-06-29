# Upstream contribution drafts (M3)

Ready-to-file drafts for the genuine findings (see [`../findings-m2.md`](../findings-m2.md)
for the full triaged list). All are **correctness/robustness** bugs — none are
secret vulnerabilities, so they can be filed publicly. Actual filing requires
write access / a maintainer contact and is intentionally left to a human (the
session that produced these had read-only, single-repo GitHub scope).

| Draft | Target(s) | Finding | Severity |
|---|---|---|---|
| [mistletoe-crash-emphasis.md](mistletoe-crash-emphasis.md) | mistletoe | `IndexError` crash on emphasis runs | high |
| [marko-lone-list-marker-eof.md](marko-lone-list-marker-eof.md) | marko | lone list marker at EOF → paragraph | medium |
| [unclosed-fence-eof-newline.md](unclosed-fence-eof-newline.md) | markdown-it-py, marko | unclosed fence at EOF drops final newline | low/med |
| [commonmark-spec-test-proposals.md](commonmark-spec-test-proposals.md) | commonmark-spec | two under-specified LRD edge cases | spec |

Additional verified findings in `../findings-m2.md` not yet written up as
standalone drafts (same evidence, ready to expand): marko unterminated-LRD-title
fallback (M-2) and block-quote indented-code blank line (M-3); markdown-it-py
lazy-continuation-after-LRD (MI-1); shared tab partial-consumption (X-2) and
trailing-tab indented-code (X-3); mistletoe softbreak-in-alt (MT-1) and bare-`)`
list marker (MT-2).

[`reproduce.py`](reproduce.py) demonstrates the key cases with only the
third-party parsers installed (no cm-difftest dependency).

## Before filing (checklist per draft)
1. Re-run `reproduce.py` against the exact pinned versions.
2. Search the target's issue tracker for duplicates (web search done; confirm).
3. For shared findings, file independently on each affected project.
4. Keep titles/repros minimal; link to the spec section cited in the draft.
