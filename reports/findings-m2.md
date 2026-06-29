# Differential findings — Python CommonMark parsers (spec 0.31.2)

Findings from the cm-difftest structure-aware differential fuzzer, triaged
against the CommonMark 0.31.2 specification. Each candidate was independently
verified by an adversarial pass that reads the spec text and reasons from it
(the `cmark` 0.31.2 reference is a strong tiebreaker, **not** treated as
infallible — see §"Spec-ambiguous", where the reference itself is on the
debatable side).

**Provenance.** markdown-it-py 4.2.0 (targets 0.31.2), mistletoe 1.5.1 (declares
no spec version), marko 2.2.3 (targets 0.31.2), cmark 0.31.2 (built from source).
All comparisons in RAW mode, compared after the official `normalize_html`.

**Method.** ~4 000 mutated inputs over 8 seeds → ~1 220 divergences, **0 crashes**,
201 distinct minimized inputs → 24 root-cause clusters → adversarial spec
verification. Every input below is minimized and reproducible (deterministic
generator); a standalone, dependency-free reproducer is in
[`reports/upstream/reproduce.py`](upstream/reproduce.py).

Legend: ✅ confirmed bug · ❓ spec-ambiguous (not filed as a bug) · ⛔ not a bug.

---

## ✅ Confirmed bugs

### marko (frostming/marko 2.2.3)

**M-1 — lone list marker at EOF parsed as a paragraph.** A bullet/ordered marker
that is the last character of the input (no trailing newline) is rendered as a
paragraph instead of an empty list item.

| input | marko | expected (cmark + markdown-it-py + mistletoe) |
|---|---|---|
| `*` | `<p>*</p>` | `<ul>\n<li></li>\n</ul>` |
| `-` | `<p>-</p>` | `<ul>\n<li></li>\n</ul>` |
| `1.` | `<p>1.</p>` | `<ol>\n<li></li>\n</ol>` |

Spec: *List items* — an empty list item is permitted; with a trailing newline
(`*\n`) marko is correct, so this is an end-of-input edge case. Belongs to a
documented marko family (CHANGELOG v2.1.4 "Correct the parsing of LinkRefDef if
it is the last line but doesn't end with a line break"). Confidence: **high**.

**M-2 — unterminated title discards the whole link reference definition.**

```
[r]:"
"
```
marko → `<p>[r]:&quot;\n&quot;</p>` (drops the LRD entirely). Expected (cmark +
markdown-it-py) → `<p>&quot;</p>`: the destination-only LRD `[r]: "` registers
and line 2 `"` becomes its own paragraph. Cleaner repro:
`[foo]: /url\n"unterminated` → marko keeps the literal `[foo]: /url`, others
register the LRD. Root cause (located by the verifier): marko's
`_parse_link_dest_title` raises `ParseError` on the unterminated `"` title and
`LinkRefDef.match` returns False for the whole definition instead of falling back
to destination-only. Confidence: **high**.

**M-3 — interior blank line in indented code inside a block quote loses its
residual indentation.**

```
>>>     1
>>>      
>>>     >
```
marko collapses the interior blank line to empty (`1\n\n&gt;`); cmark +
markdown-it-py + mistletoe keep the one residual space (`1\n \n&gt;`). Spec:
*Indented code blocks* — "Any initial spaces or tabs beyond four spaces of
indentation will be included in the content, even in interior blank lines." Only
triggers inside a block quote (the bare indented-code example is fine in marko).
Confidence: **high**.

### markdown-it-py (4.2.0)

**MI-1 — lazy continuation after a link reference definition inside a block
quote.**

```
>[f]:/
)
```
markdown-it-py (and marko) close the block quote early and emit `)` as a
top-level paragraph; cmark keeps it inside (`<blockquote><p>)</p></blockquote>`).
Isolated repro (no `)` quirk): `>[foo]: /url\nbar` — cmark and mistletoe put
`bar` inside the block quote; markdown-it-py and marko put it outside. Spec:
*Block quotes* laziness rule. Confidence: **high**. (Affects markdown-it-py and
marko.)

### markdown-it-py + marko (shared)

**X-1 — unclosed fenced code block at EOF drops the final newline.**

```
~~~
t
```
markdown-it-py and marko → `<pre><code>t</code></pre>` (no trailing newline);
cmark and mistletoe → `<pre><code>t\n</code></pre>`. With a trailing newline
(`~~~\nt\n`) all four agree, and indented code at EOF is fine in both — so this
is specifically the unclosed-fence-at-EOF path. Spec: a line may end "by the end
of file" (line 306–308); content lines render with a trailing newline.
Confidence: **high**.

### markdown-it-py + mistletoe (shared)

**X-2 — partially-consumed tab after a block-quote marker drops a leading
space.**

```
>>  <TAB><
```
markdown-it-py and mistletoe → `<pre><code>&lt;` (no leading space); cmark and
marko → `<pre><code> &lt;` (one leading space). The pure-space equivalent
`>>      <` renders identically in all four, proving a tab-expansion bug. Spec:
*Tabs* (tab stop 4; partial-consumption example `>→→foo`). Confidence: **high**.

### mistletoe (1.5.1)

**MT-1 — soft line break dropped inside image `alt` text.**

```
![
]()
```
mistletoe → `<img src="" alt="">` (softbreak deleted); the spec permits a
softbreak in `alt` to render as a space *or* a line ending, not to vanish.
`![a\nb]()` → mistletoe `alt="ab"` (words glued together). cmark `alt=" "`,
markdown-it-py/marko `alt="\n"` are both conformant. Confidence: **high**.

**MT-2 — bare `)` parsed as a list marker.** Single input `)` → mistletoe
`<ul>\n<li></li>\n</ul>`; everyone else `<p>)</p>`. An ordered-list marker is
1–9 digits followed by `.`/`)`; a lone `)` is not a marker (and `<ul>` would be
wrong even if it were). Confidence: **high**.

**MT-3 — CRASH (`IndexError`) on certain emphasis-delimiter runs.** *Highest
severity (spec §3: a parser of untrusted input must never crash).*

Minimal input (1-minimal under ddmin and char-level reduction):

```
****"************+****
```

mistletoe raises `IndexError: string index out of range`; markdown-it-py, marko,
and cmark all render it without error. Root cause (located via the traceback):
`mistletoe/core_tokens.py:117` in `process_emphasis`:

```python
bottom = star_bottom if closer.type[0] == '*' else underscore_bottom
```

`closer.type` is the empty string for one delimiter in this configuration, so
`closer.type[0]` indexes out of range. Found by the Atheris coverage-guided
target after ~262 k executions. Confidence: **high** (deterministic repro).

### mistletoe + marko (shared)

**X-3 — trailing tab-bearing blank line leaks into an indented code block.**

```
<TAB>]
<TAB><SPACE>
```
mistletoe and marko keep the trailing all-whitespace line in the code block;
cmark and markdown-it-py drop it. The all-spaces equivalent is handled correctly
by all four — the defect is in treating a *tab*-bearing line as blank. Spec:
"Blank lines … following an indented code block are not included in it" + the
blank-line definition (only spaces/tabs). Confidence: **high**.

---

## ❓ Spec-ambiguous (candidates for a CommonMark clarification, not filed as bugs)

**A-1 — a type-7 HTML block immediately after a link reference definition.**

```
[À]:x
<e>
```
cmark → `<p><e></p>` (treats the LRD line as an open paragraph that type-7 HTML
may not interrupt); markdown-it-py, marko, mistletoe → `<e>` (fresh HTML block).
The non-ASCII `À` is incidental (`[foo]:x\n<e>` reproduces it). The spec has no
governing example for "type-7 HTML directly after an LRD", and the appendix
parsing-strategy note ("reference definitions are detected when a paragraph is
closed", line ~9503) can be read either way. Defensible both ways → not a bug.
**Good candidate for a new `commonmark/commonmark-spec` test case.**

**A-2 — an empty list item immediately after a link reference definition.**

```
[r]:/
*
```
cmark + marko → `<p>*</p>`; markdown-it-py + mistletoe → `<ul><li></li></ul>`.
Hinges on whether the in-progress LRD counts as an "open paragraph" for the
"empty list item cannot interrupt a paragraph" rule. The appendix (line ~9503)
supports cmark's paragraph-buffering model, so **the reference is on a defensible
side and we do _not_ classify this as a cmark bug** — it is a genuine
under-specification. (Note: the *standalone* `*` with no preceding LRD is
unambiguous and is the M-1 marko bug above.) Also a spec-clarification candidate.

---

## ⛔ Not bugs (by-design, excluded from filing)

- `[](javascript:)`, `[x]:javascript:` — markdown-it-py's `validateLink` rejects
  dangerous schemes and marko rewrites them to `#harmful-link`. These are
  documented, configurable **security defaults**, not spec violations (CommonMark
  performs no URL-scheme sanitization). They belong to the Phase 3 security
  comparison, run separately in a single safety mode — never mixed with
  compliance. Nothing here is a *secret* vulnerability requiring private
  disclosure (the sanitizers are public, intended behavior), so no findings are
  withheld.
- Exact percent-encoding of some URL characters (e.g. `;`, `%`) where the spec
  under-specifies normalization — tracked but not asserted as bugs pending the
  second verification pass.

---

## Crash class (spec §3, §8)

The in-process **differential** campaign (~4 000 inputs) found **0 crashes** —
the expected outcome for hardened parsers (spec §8). The **Atheris** (libFuzzer)
coverage-guided target, however, surfaced a genuine **mistletoe crash** after
~262 k executions (finding **MT-3** above) — a vindication of running both
generation sources rather than relying on differential signal alone. (An earlier
Atheris run also caught a bug in *our own* harness target — invalid-UTF-8 decode
— now fixed and regression-tested.) Per §8, crash signal is a bonus; here it paid
off with the single highest-severity finding of the campaign.

## Upstream status (M3)

These are correctness bugs (not security), so they can be filed publicly.
Ready-to-file issue drafts and a standalone reproducer live under
`reports/upstream/`. Actual filing requires repo write access / maintainer
contact and is left to the maintainer of this project (the session's GitHub
integration is scoped to read-only on a single repo). Before filing, each draft
notes a duplicate-search of the target's tracker.
