# [commonmark-spec] Proposed test cases for two under-specified edge cases

**Target:** commonmark/commonmark-spec (spec 0.31.2)

The differential harness found two inputs where compliant implementations split
into two defensible camps and the spec text does not decide the outcome. Rather
than file these as parser bugs, we propose them as spec test cases /
clarifications. For each, the two camps are noted; the spec maintainers should
pick the intended behavior and add a conformance example.

## Proposal 1 — a type-7 HTML block immediately after a link reference definition

```
[foo]:x
<e>
```

- **camp A — `<p><e></p>`:** `cmark` 0.31.2. The link reference definition text
  is held in an "open paragraph" until the paragraph closes (Appendix, "reference
  definitions are detected when a paragraph is closed"), and a type-7 HTML block
  *may not interrupt a paragraph*, so `<e>` is absorbed; the LRD is stripped at
  close, leaving `<p><e></p>`.
- **camp B — `<e>`:** `markdown-it-py` 4.2.0, `marko` 2.2.3, `mistletoe` 1.5.1.
  The LRD is recognized eagerly, leaving no open paragraph, so `<e>` starts a
  fresh type-7 HTML block.

The spec has no example for "type-7 HTML directly after an LRD with no blank
line". A conformance example would settle it.

## Proposal 2 — an empty list item immediately after a link reference definition

```
[r]:/
*
```

- **camp A — `<p>*</p>`:** `cmark` 0.31.2, `marko` 2.2.3. The in-progress LRD
  counts as an open paragraph, and "an empty list item cannot interrupt a
  paragraph", so `*` is paragraph text.
- **camp B — `<ul><li></li></ul>`:** `markdown-it-py` 4.2.0, `mistletoe` 1.5.1.
  No open paragraph remains after the LRD, so the empty marker starts a list.

Note the standalone `*` (no preceding LRD) is unambiguous — all of cmark,
markdown-it-py, and mistletoe produce the empty list — so this case is purely
about the LRD/open-paragraph interaction.

Both proposals reduce to the same underlying question: **does an in-progress link
reference definition constitute an "open paragraph" for the purpose of the
block-interruption rules?** One clarifying sentence in the spec plus two examples
would remove the ambiguity.
