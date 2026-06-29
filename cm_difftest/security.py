"""Security comparison — sanitization-bypass / XSS divergences (spec §6, Phase 3).

The highest-value finding is a parser that, in its safe configuration, emits an
executable sink (a ``javascript:`` href, an unescaped ``<script>``, an event
handler) where its own sanitizer is supposed to neutralize it. This module:

* detects executable sinks the way a *browser* would resolve them — decoding HTML
  entities and stripping the ASCII control/space characters that browsers ignore
  inside a URL scheme — so obfuscated bypasses (``java&#9;script:``,
  ``java&#58;``, ``JaVaScRiPt:``) are caught, not just literal ones;
* records each parser's **safety posture** (which sink classes its safe config is
  expected to neutralize), so "leaks" from a parser that never claimed to
  sanitize (mistletoe; marko for raw HTML) are reported as posture, not as
  bypasses;
* flags a **bypass** only when a parser emits a sink its posture says it should
  have removed — and cross-checks against cmark's safe mode (the strict
  baseline).

Disclosure discipline (spec §6): genuine bypass findings are written to the
git-ignored ``findings/`` directory and treated as private until responsibly
disclosed. This module never publishes anything.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass, field

from cm_difftest.adapters import Mode, default_adapters

__all__ = [
    "detect_sinks",
    "POSTURE",
    "SecurityResult",
    "scan",
    "DANGEROUS_SCHEMES",
    "generate_vectors",
    "scan_campaign",
]

DANGEROUS_SCHEMES = ("javascript:", "vbscript:", "data:text/html")

# href/src attribute (double/single/unquoted) and dangerous standalone tags.
_ATTR_RE = re.compile(r"""\b(?:href|src)\s*=\s*("([^"]*)"|'([^']*)'|([^\s>]+))""", re.I)
_DANGER_TAG_RE = re.compile(r"<\s*(script|iframe|object|embed|svg|math)\b", re.I)
_HANDLER_RE = re.compile(r"<[^>]*?\son[a-z]+\s*=", re.I)
_CTRL_WS_RE = re.compile(r"[\x00-\x20]+")


def _browser_normalize_url(value: str) -> str:
    """Approximate how a browser resolves a URL scheme: decode entities, drop
    ASCII control/space characters, lowercase."""
    decoded = _html.unescape(value)
    return _CTRL_WS_RE.sub("", decoded).lower()


def detect_sinks(html_out: str) -> set[str]:
    """Return the set of executable-sink categories present in *html_out*."""
    if not html_out:
        return set()
    sinks: set[str] = set()
    if _DANGER_TAG_RE.search(html_out):
        sinks.add("dangerous_tag")
    if _HANDLER_RE.search(html_out):
        sinks.add("event_handler")
    for m in _ATTR_RE.finditer(html_out):
        raw = m.group(2) or m.group(3) or m.group(4) or ""
        norm = _browser_normalize_url(raw)
        if any(norm.startswith(s) for s in DANGEROUS_SCHEMES):
            sinks.add("dangerous_url")
    return sinks


# What each parser's safe configuration is *expected* to neutralize. A sink in
# this set that nonetheless appears is a genuine bypass; a sink outside it is the
# parser's (documented) posture, not a bug.
POSTURE: dict[str, set[str]] = {
    # html=False escapes all raw HTML; validateLink rejects dangerous URL schemes
    "markdown-it-py": {"dangerous_tag", "event_handler", "dangerous_url"},
    # safe mode scrubs raw HTML and blanks dangerous links
    "cmark": {"dangerous_tag", "event_handler", "dangerous_url"},
    # rewrites dangerous URL schemes to #harmful-link; raw HTML passes through
    "marko": {"dangerous_url"},
    # no sanitizer at all
    "mistletoe": set(),
}


@dataclass
class SecurityResult:
    markdown: str
    sinks: dict[str, set]  # parser -> sink categories emitted (safe mode)
    bypasses: dict[str, set]  # parser -> sink categories it should have removed but didn't
    renders: dict[str, str] = field(default_factory=dict)

    @property
    def has_bypass(self) -> bool:
        return any(self.bypasses.values())

    def offenders(self) -> list[str]:
        return sorted(p for p, b in self.bypasses.items() if b)


# --- Vector generation (structure-aware, obfuscation-heavy) ------------------ #

_PAYLOADS = ["alert(1)", "alert(document.domain)", "msgbox(1)", "//x", ""]
_BASE_SCHEMES = ["javascript:", "vbscript:", "data:text/html,", "data:text/html;base64,"]


def _obfuscations(scheme: str) -> list[str]:
    """Return obfuscated spellings of a dangerous scheme a browser still honors."""
    out = {scheme, scheme.upper(), scheme.capitalize()}
    # control/whitespace injected into the scheme (browsers strip these)
    for ws in ("\t", "\n", "\r", " ", "\x01"):
        out.add(scheme[:4] + ws + scheme[4:])
        out.add(ws + scheme)
    # entity-encoded colon and leading letter
    out.add(scheme.replace(":", "&#58;"))
    out.add(scheme.replace(":", "&#x3a;"))
    if scheme[:1].isalpha():
        out.add("&#%d;%s" % (ord(scheme[0]), scheme[1:]))
        out.add("&#x%x;%s" % (ord(scheme[0]), scheme[1:]))
    return list(out)


def _templates(url: str) -> list[str]:
    return [
        f"[x]({url})",
        f"[x]({url} \"t\")",
        f"![img]({url})",
        f"<{url}>",
        f"[x](<{url}>)",
        f"[x][r]\n\n[r]: {url}",
        f"[x][r]\n\n[r]: <{url}>",
    ]


def generate_vectors(seed: int = 0, *, mutate: bool = True, max_mutations: int = 2):
    """Yield security test inputs: dangerous schemes × obfuscations × templates,
    optionally perturbed with the structure-aware mutators (deterministic)."""
    import random

    from cm_difftest.fuzz.mutators import mutate_once

    rng = random.Random(seed)
    base: list[str] = []
    for sch in _BASE_SCHEMES:
        for ob in _obfuscations(sch):
            for pay in _PAYLOADS:
                url = ob + pay
                base.extend(_templates(url))
    for md in base:
        yield md
        if mutate:
            text = md
            for _ in range(rng.randint(1, max_mutations)):
                _, text = mutate_once(text, rng)
            yield text


def scan_campaign(iterations: int = 4000, seed: int = 0, adapters=None) -> dict:
    """Scan generated vectors; collect genuine bypasses and posture statistics."""
    adapters = adapters if adapters is not None else default_adapters()
    bypasses: list[dict] = []
    leak_counts: dict[str, int] = {a.name: 0 for a in adapters}
    scanned = 0
    for md in generate_vectors(seed=seed):
        if scanned >= iterations:
            break
        scanned += 1
        r = scan(md, adapters)
        for name, s in r.sinks.items():
            if s:
                leak_counts[name] += 1
        if r.has_bypass:
            bypasses.append(
                {
                    "input": md,
                    "input_repr": repr(md),
                    "bypasses": {p: sorted(b) for p, b in r.bypasses.items() if b},
                    "renders": r.renders,
                }
            )
    return {
        "scanned": scanned,
        "seed": seed,
        "bypasses": bypasses,
        "leak_counts": leak_counts,
        "posture": {k: sorted(v) for k, v in POSTURE.items()},
    }


def scan(markdown: str, adapters=None) -> SecurityResult:
    """Render *markdown* through every parser's safe config and find bypasses."""
    adapters = adapters if adapters is not None else default_adapters()
    sinks: dict[str, set] = {}
    bypasses: dict[str, set] = {}
    renders: dict[str, str] = {}
    for a in adapters:
        try:
            out = a.render(markdown, mode=Mode.SAFE)
        except Exception as exc:  # noqa: BLE001 - a crash is its own finding class
            renders[a.name] = f"[error] {type(exc).__name__}: {exc}"
            sinks[a.name] = set()
            bypasses[a.name] = set()
            continue
        renders[a.name] = out
        s = detect_sinks(out)
        sinks[a.name] = s
        expected = POSTURE.get(a.name, set())
        bypasses[a.name] = s & expected
    return SecurityResult(markdown=markdown, sinks=sinks, bypasses=bypasses, renders=renders)
