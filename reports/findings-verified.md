## Adversarially-verified findings — full list

Every candidate below was verified by an independent agent reasoning from the
CommonMark 0.31.2 spec text (cmark as a strong-but-not-absolute tiebreaker).
Distinct cases: **36** → 25 confirmed bugs (offender targets the
spec), plus the categories the harness correctly *excluded*.

### Confirmed bugs

| input (repr) | likely-wrong | spec area |
|---|---|---|
| `'[`t`>`'` | markdown-it-py | Code spans |
| `'- ```\n\n- `'` | markdown-it-py | Lists — loose/tight definition, spec-0.31. |
| `"[`.`>`](; 't')"` | markdown-it-py | Links, "A link text consists of...": rule  |
| `'* [a]:v\na'` | markdown-it-py and marko | List items, Laziness rule #5 |
| `'~~~\nt'` | markdown-it-py, marko | "Fenced code blocks" |
| `'>[f]:/\n)'` | markdown-it-py, marko, mistletoe | Block quotes — laziness rule |
| `'>>  \t<'` | markdown-it-py, mistletoe | Tabs section, spec lines 409-425 |
| `'>>  \t>'` | markdown-it-py, mistletoe | Tabs |
| `'>\n    >'` | markdown-it-py, mistletoe | Block quotes |
| `'*'` | marko | List items, example "A list may start or e |
| `'[r]:"\n"'` | marko | "Link reference definitions" |
| `'>>>     1\n>>>      \n>>>     >'` | marko | Indented code blocks |
| `'<!'` | marko | HTML blocks, start condition type 4 |
| `'-'` | marko | "Lists" / "List items" — section on empty  |
| `'1.'` | marko | List items, Rule #3 "Item starting with a  |
| `'>>>  -    >\n>>>\n>>>      o'` | marko | List items, rule #1 |
| `'   -\n    \t -\n    '` | marko | Tabs |
| `'\\` `\\`'` | marko | Code spans |
| `'[`]`]()'` | marko | "Code spans" precedence note |
| `'-\xa0--'` | marko (and mistletoe, which declares no spec ver | Leaf blocks > Thematic breaks |
| `'_\u2028_'` | marko, mistletoe | Character class definitions, lines 319-321 |
| `'[](( )'` | marko, mistletoe | Links — link destination definition, spec  |
| `'**`<`<ps:**>'` | marko, mistletoe | Code spans — precedence |
| `'![\n]()'` | mistletoe | Soft line breaks section |
| `'\t]\n\t '` | mistletoe, marko | Indented code blocks, example "Blank lines |

### Reference-implicated (treated as spec-ambiguous, NOT filed against cmark)

Cases where an agent implicated `cmark` itself; all involve the same
link-reference-definition / empty-list / lazy-continuation interaction the spec
under-specifies. We do not assert these as cmark bugs (§5).

| input (repr) | likely-wrong | spec area |
|---|---|---|
| `'[r]:/\n*'` | cmark, marko | Link reference definitions |
| `'>o\n*'` | markdown-it-py and cmark | Section 5.2 "List items", Exception 1 |
| `'\xa0'` | markdown-it-py and marko (also mistletoe); cmark | "Characters and lines": blank-line definit |

### Spec-ambiguous (proposed as clarifications, not bugs)

| input (repr) | likely-wrong | spec area |
|---|---|---|
| `'[À]:x\n<e>'` | none | HTML blocks |
| `"[](')"` | none | "Links" — link destination definition |
| `'[](;)'` | none | Links / Link destination |
| `'[](%)'` | none | Inlines > Links: link destination definiti |

### Not bugs (by-design / renderer latitude)

| input (repr) | likely-wrong | spec area |
|---|---|---|
| `'[x]:javascript:'` | markdown-it-py | Link reference definitions |
| `'[](javascript:)'` | none | Links: "A link text consists of a sequence |
| `'<!A'` | none | HTML blocks, start/end conditions, type 4 |
| `'><!--\nz\n>'` | none | HTML blocks |
