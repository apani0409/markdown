# CommonMark compliance scorecard — spec 0.31.2

_Generated: 2026-06-29_

Per-parser pass/fail against the official CommonMark `spec.txt` (652 examples), compared after the official `normalize_html`.

## Provenance

| Parser | Library version | Target spec | Role |
|---|---|---|---|
| markdown-it-py | 4.2.0 | 0.31.2 | SUT |
| mistletoe | 1.5.1 | not declared | SUT |
| marko | 2.2.3 | 0.31.2 | SUT |
| cmark | 0.31.2 | 0.31.2 | reference (oracle) |

## Overall

| Parser | Passed | Total | Pass rate |
|---|---:|---:|---:|
| markdown-it-py | 652 | 652 | 100.0% |
| mistletoe | 628 | 652 | 96.3% |
| marko | 652 | 652 | 100.0% |
| cmark | 652 | 652 | 100.0% |

## M1 done-criterion (normalization false positives)

- Reference (`cmark`) matches spec.txt on **652/652** examples.
- Normalizer false-positive rate: **0.0%** (0 example(s)).
- Comparisons classified as normalization artifacts: **0**.

## By section

| Section | markdown-it-py | mistletoe | marko | cmark |
|---|---:|---:|---:|---:|
| Tabs | 11/11 | 11/11 | 11/11 | 11/11 |
| Backslash escapes | 13/13 | 11/13 | 13/13 | 13/13 |
| Entity and numeric character references | 17/17 | 15/17 | 17/17 | 17/17 |
| Precedence | 1/1 | 1/1 | 1/1 | 1/1 |
| Thematic breaks | 19/19 | 19/19 | 19/19 | 19/19 |
| ATX headings | 18/18 | 18/18 | 18/18 | 18/18 |
| Setext headings | 27/27 | 26/27 | 27/27 | 27/27 |
| Indented code blocks | 12/12 | 12/12 | 12/12 | 12/12 |
| Fenced code blocks | 29/29 | 29/29 | 29/29 | 29/29 |
| HTML blocks | 44/44 | 44/44 | 44/44 | 44/44 |
| Link reference definitions | 27/27 | 24/27 | 27/27 | 27/27 |
| Paragraphs | 8/8 | 8/8 | 8/8 | 8/8 |
| Blank lines | 1/1 | 1/1 | 1/1 | 1/1 |
| Block quotes | 25/25 | 25/25 | 25/25 | 25/25 |
| List items | 48/48 | 48/48 | 48/48 | 48/48 |
| Lists | 26/26 | 26/26 | 26/26 | 26/26 |
| Inlines | 1/1 | 1/1 | 1/1 | 1/1 |
| Code spans | 22/22 | 21/22 | 22/22 | 22/22 |
| Emphasis and strong emphasis | 132/132 | 125/132 | 132/132 | 132/132 |
| Links | 90/90 | 89/90 | 90/90 | 90/90 |
| Images | 22/22 | 21/22 | 22/22 | 22/22 |
| Autolinks | 19/19 | 19/19 | 19/19 | 19/19 |
| Raw HTML | 20/20 | 14/20 | 20/20 | 20/20 |
| Hard line breaks | 15/15 | 15/15 | 15/15 | 15/15 |
| Soft line breaks | 2/2 | 2/2 | 2/2 | 2/2 |
| Textual content | 3/3 | 3/3 | 3/3 | 3/3 |

## Failing examples (SUTs)

### markdown-it-py — 0 failing

_None — fully compliant._

### mistletoe — 24 failing

| # | Section | Category | Flags |
|---:|---|---|---|
| 12 | Backslash escapes | spec_noncompliance | possible_version_skew |
| 14 | Backslash escapes | spec_noncompliance | possible_version_skew |
| 27 | Entity and numeric character references | spec_noncompliance | possible_version_skew |
| 41 | Entity and numeric character references | spec_noncompliance | possible_version_skew |
| 91 | Setext headings | spec_noncompliance | possible_version_skew |
| 209 | Link reference definitions | spec_noncompliance | possible_version_skew |
| 210 | Link reference definitions | spec_noncompliance | possible_version_skew |
| 211 | Link reference definitions | spec_noncompliance | possible_version_skew |
| 343 | Code spans | spec_noncompliance | possible_version_skew |
| 352 | Emphasis and strong emphasis | spec_noncompliance | possible_version_skew |
| 354 | Emphasis and strong emphasis | spec_noncompliance | possible_version_skew |
| 359 | Emphasis and strong emphasis | spec_noncompliance | possible_version_skew |
| 363 | Emphasis and strong emphasis | spec_noncompliance | possible_version_skew |
| 380 | Emphasis and strong emphasis | spec_noncompliance | possible_version_skew |
| 385 | Emphasis and strong emphasis | spec_noncompliance | possible_version_skew |
| 395 | Emphasis and strong emphasis | spec_noncompliance | possible_version_skew |
| 508 | Links | spec_noncompliance | possible_version_skew |
| 590 | Images | spec_noncompliance | possible_version_skew |
| 619 | Raw HTML | spec_noncompliance | possible_version_skew |
| 620 | Raw HTML | spec_noncompliance | possible_version_skew |
| 624 | Raw HTML | spec_noncompliance | possible_version_skew |
| 625 | Raw HTML | spec_noncompliance | possible_version_skew |
| 626 | Raw HTML | spec_noncompliance | possible_version_skew |
| 632 | Raw HTML | spec_noncompliance | possible_version_skew |

### marko — 0 failing

_None — fully compliant._
