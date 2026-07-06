# Phase 3 — Security comparison (sanitization / XSS posture, spec §6)

Differential comparison of how the parsers handle dangerous content in their
**safe** configuration, looking for the highest-value class of finding: a
sanitization bypass where one parser emits an executable sink (a `javascript:`
href, an unescaped `<script>`, an event handler) that its own sanitizer is
supposed to remove.

## Method

- **Safe configs (recorded, apples-to-apples):** markdown-it-py `html=False`
  (escapes raw HTML) + its `validateLink` (rejects dangerous URL schemes); cmark
  default options (scrubs raw HTML, blanks dangerous links); marko default
  (rewrites dangerous URLs to `#harmful-link`, passes raw HTML); mistletoe
  default (no sanitizer).
- **Browser-accurate sink detection:** rendered output is scanned for executable
  sinks the way a browser resolves them — HTML entities decoded and ASCII
  control/space characters stripped from URL schemes — so obfuscated vectors
  (`java&#9;script:`, `javascript&#58;`, `JaVaScRiPt:`, control chars) are
  caught, not only literal ones.
- **Vectors:** dangerous schemes (`javascript:`, `vbscript:`, `data:text/html`,
  `data:text/html;base64`) × obfuscations (case, entity-encoded colon/letter,
  injected tab/newline/space/control) × link / image / autolink / angle-bracket /
  reference-definition templates, then perturbed with the structure-aware
  mutators. **18 000 vectors** over 6 seeds. Reproduce with `cm-difftest security`.

## Result: zero sanitizer bypasses

Across 18 000 structure-aware obfuscated vectors, **no genuine bypass was found**:
no parser emitted an executable sink that its safe configuration is supposed to
remove.

| Parser | Safe posture | Sink emissions / 18 000 | Bypasses |
|---|---|---:|---:|
| markdown-it-py | escapes HTML + validates URLs | 0 | **0** |
| cmark (ref) | scrubs HTML + blanks dangerous URLs | 0 | **0** |
| marko | sanitizes URLs (`#harmful-link`); **passes raw HTML** | 74 (all raw-HTML tags) | **0** |
| mistletoe | **no sanitizer** | 7 367 (mostly live `javascript:`/`data:` URLs) | n/a |

The marko emissions are exclusively `dangerous_tag` (raw HTML passed through) —
**zero** `dangerous_url`, i.e. its URL sanitizer was never defeated. mistletoe's
emissions are its documented posture (it has no sanitizer), not a bypass.

## Security posture notes (for downstream users)

- **markdown-it-py** and **cmark** are safe to render untrusted Markdown with the
  configs above; their sanitizers withstood every obfuscation tried.
- **marko** robustly neutralizes dangerous URL schemes, but **passes raw HTML
  through** — do not rely on it to sanitize embedded HTML; post-sanitize (e.g.
  with `nh3`/`bleach`) if the input is untrusted.
- **mistletoe** performs **no sanitization** — it emits live `javascript:` /
  `data:text/html` links and raw HTML/`<script>`. ~42% of dangerous vectors
  produced an executable sink. Output of untrusted input **must** be sanitized
  downstream before rendering in a browser.

## Disclosure

No bypass — therefore **no secret vulnerability** to disclose. The mistletoe and
marko behaviors above are known, by-design posture (mistletoe is not advertised
as a sanitizer), so they are documented publicly here rather than withheld. Had a
bypass been found, it would have been written to the git-ignored `findings/`
directory and disclosed privately to the maintainer first (spec §6); the
`cm-difftest security` command does exactly that when it finds one.
