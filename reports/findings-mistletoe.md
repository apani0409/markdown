# mistletoe deep-dive (the least CommonMark-compliant SUT)

mistletoe 1.5.1 was the only SUT with static-corpus failures (628/652) and the
most differential findings, so a focused campaign collected mistletoe-offender
divergences (365 distinct minimized inputs → 65 clusters, 18 mistletoe-only).
Below: the distinct, adversarially-cross-checked bug classes where mistletoe is
the **sole** outlier (cmark 0.31.2, markdown-it-py 4.2.0, and marko 2.2.3 all
agree on the spec-correct output). All verified in RAW mode after the official
normalizer.

## Flavor finding (characterization, not a parser bug)

**mistletoe enables GFM strikethrough (`~~…~~`) by default**, so its default
renderer is **CommonMark + an extension**, not pure CommonMark:

```
~~ ~~   mistletoe -> <p><del> </del></p>     others -> <p>~~ ~~</p>
```

This matters for any "pure CommonMark" comparison and partly explains its
static-corpus gaps. Not filed as a bug — it is a deliberate extension — but users
who want strict CommonMark must account for it.

## Confirmed bugs (mistletoe sole outlier)

| input (repr) | mistletoe | spec-correct (cmark + 2 others) | issue |
|---|---|---|---|
| `'.'` | `<ul><li></li></ul>` | `<p>.</p>` | a lone `.` is **not** a list marker (ordered marker needs a digit) |
| `'*\n2'` | `<ul><li>2</li></ul>` | `<ul><li></li></ul><p>2</p>` | text after an empty list item wrongly absorbed as item content |
| `'>r\n>='` | `<blockquote><p>r\n=</p></blockquote>` | `<blockquote><h1>r</h1></blockquote>` | setext heading not recognized inside a block quote |
| `'*£*b'` | `<p><em>£</em>b</p>` | `<p>*£*b</p>` | emphasis opened across a non-ASCII char that fails the flanking rule |
| `'\\\r«'` | `<p>\\\r\n«</p>` | `<p><br />\n«</p>` | backslash hard line break not recognized before a CR line ending |
| `'<hs:\t>'` | `<p><a href="hs:%09">…</a></p>` | `<p>&lt;hs:\t&gt;</p>` | autolink wrongly accepts a tab (autolinks may not contain whitespace) |

Plus the general quote-escaping deviation noted elsewhere: mistletoe renders a
literal `"` in text where the spec/cmark emit `&quot;` (valid HTML, but diverges
from the conformance comparison).

These are in addition to the mistletoe findings in
[`findings-m2.md`](findings-m2.md) (the `IndexError` crash, soft-break dropped in
`alt`, bare `)` as a list marker, tab partial-consumption). The lone-`.` and
bare-`)` cases share a root: over-eager list-marker recognition.

Reproduce the collection with `cm-difftest fuzz --require-offenders mistletoe`.
