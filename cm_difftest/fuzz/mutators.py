"""Structure-aware Markdown mutation operators (spec §8).

Each operator takes ``(text, rng)`` and returns a mutated string. Operators
mutate at the *syntax* level (emphasis runs, blockquote/list nesting, links/
images/reference definitions, HTML blocks, code fences, entity references,
escapes, tricky whitespace/unicode) rather than flipping random bytes — this is
what surfaces differential (correctness) divergences, which are far more
abundant than crashes (spec §8). Operators must never raise.
"""
from __future__ import annotations

import random
from collections.abc import Callable

__all__ = ["MUTATORS", "mutate_once", "Mutator"]

Mutator = Callable[[str, random.Random], str]

# Tokens used by several operators.
_EMPHASIS = ["*", "_", "**", "__", "***", "~~", "`", "``"]
_ENTITIES = ["&amp;", "&lt;", "&gt;", "&quot;", "&#42;", "&#x2A;", "&notreal;", "&#0;", "&#xFFFFFF;"]
_HTML_BITS = ["<b>", "</b>", "<div>", "</div>", "<!-- c -->", "<a href=\"x\">", "<script>", "</script>", "<![CDATA[x]]>"]
_URLS = ["http://x", "javascript:alert(1)", "data:text/html,x", "/a b", "<x y>", "(x)", "#frag", "mailto:a@b"]
_PUNCT = ["\\", "[", "]", "(", ")", "!", "*", "_", "`", "~", "<", ">", "&", "|", "#", "+", "-"]


def _lines(text: str) -> list[str]:
    return text.split("\n")


def _pos(text: str, rng: random.Random) -> int:
    return rng.randint(0, len(text)) if text else 0


def m_insert_emphasis(text: str, rng: random.Random) -> str:
    tok = rng.choice(_EMPHASIS)
    i = _pos(text, rng)
    return text[:i] + tok + text[i:]


def m_wrap_emphasis(text: str, rng: random.Random) -> str:
    tok = rng.choice(_EMPHASIS)
    return f"{tok}{text}{tok}"


def m_perturb_runs(text: str, rng: random.Random) -> str:
    """Add or drop one char from a random run of * _ ~ or `."""
    if not text:
        return rng.choice(_EMPHASIS)
    i = rng.randrange(len(text))
    c = text[i]
    if c in "*_~`":
        if rng.random() < 0.5:
            return text[:i] + c + text[i:]  # lengthen the run
        return text[:i] + text[i + 1 :]  # shorten the run
    return text[:i] + rng.choice("*_~`") + text[i:]


def m_blockquote(text: str, rng: random.Random) -> str:
    depth = rng.randint(1, 3)
    prefix = "> " * depth
    return "\n".join(prefix + ln for ln in _lines(text))


def m_listify(text: str, rng: random.Random) -> str:
    marker = rng.choice(["- ", "+ ", "* ", "1. ", "2) "])
    return "\n".join(marker + ln for ln in _lines(text))


def m_indent(text: str, rng: random.Random) -> str:
    pad = rng.choice(["    ", "\t", "  ", " \t "])
    return "\n".join(pad + ln for ln in _lines(text))


def m_code_fence(text: str, rng: random.Random) -> str:
    fence = rng.choice(["```", "~~~", "````", "``` info"])
    close = fence.split(" ")[0]
    return f"{fence}\n{text}\n{close}"


def m_insert_html(text: str, rng: random.Random) -> str:
    bit = rng.choice(_HTML_BITS)
    i = _pos(text, rng)
    return text[:i] + bit + text[i:]


def m_insert_entity(text: str, rng: random.Random) -> str:
    ent = rng.choice(_ENTITIES)
    i = _pos(text, rng)
    return text[:i] + ent + text[i:]


def m_make_link(text: str, rng: random.Random) -> str:
    url = rng.choice(_URLS)
    label = text if len(text) < 40 else text[:40]
    bang = "!" if rng.random() < 0.3 else ""
    title = rng.choice(["", ' "t"', " 't'", " (t)"])
    return f"{bang}[{label}]({url}{title})"


def m_reference_def(text: str, rng: random.Random) -> str:
    url = rng.choice(_URLS)
    label = rng.choice(["ref", "a", "x y", "À"])
    use = f"[{label}]"
    define = f"[{label}]: {url}"
    if rng.random() < 0.5:
        return f"{use}\n\n{define}\n{text}"
    return f"{text}\n\n{use}\n{define}"


def m_backslash_escape(text: str, rng: random.Random) -> str:
    if not text:
        return "\\" + rng.choice(_PUNCT)
    i = rng.randrange(len(text))
    return text[:i] + "\\" + text[i:]


def m_insert_punct(text: str, rng: random.Random) -> str:
    p = rng.choice(_PUNCT) * rng.randint(1, 4)
    i = _pos(text, rng)
    return text[:i] + p + text[i:]


def m_tricky_whitespace(text: str, rng: random.Random) -> str:
    ws = rng.choice(["\t", "   ", " ", " \n ", "\r\n", "\n\n", "  \n"])
    i = _pos(text, rng)
    return text[:i] + ws + text[i:]


def m_tricky_unicode(text: str, rng: random.Random) -> str:
    ch = rng.choice(["​", "́", "‍", "﻿", " ", "à", "𝐀", "\x00", "‘"])
    i = _pos(text, rng)
    return text[:i] + ch + text[i:]


def m_duplicate_fragment(text: str, rng: random.Random) -> str:
    if not text:
        return text
    a = rng.randrange(len(text))
    b = rng.randint(a, len(text))
    frag = text[a:b]
    i = _pos(text, rng)
    return text[:i] + frag + text[i:]


def m_delete_fragment(text: str, rng: random.Random) -> str:
    if len(text) < 2:
        return text
    a = rng.randrange(len(text))
    b = rng.randint(a + 1, len(text))
    return text[:a] + text[b:]


def m_imbalance_brackets(text: str, rng: random.Random) -> str:
    ch = rng.choice("[]()")
    i = _pos(text, rng)
    return text[:i] + ch * rng.randint(1, 3) + text[i:]


# Weighted operator table: emphasis / links / html / entities are weighted
# higher because that is where divergences cluster (per the M1 scorecard).
MUTATORS: list[tuple[str, Mutator, int]] = [
    ("insert_emphasis", m_insert_emphasis, 4),
    ("wrap_emphasis", m_wrap_emphasis, 3),
    ("perturb_runs", m_perturb_runs, 4),
    ("blockquote", m_blockquote, 2),
    ("listify", m_listify, 2),
    ("indent", m_indent, 2),
    ("code_fence", m_code_fence, 2),
    ("insert_html", m_insert_html, 4),
    ("insert_entity", m_insert_entity, 3),
    ("make_link", m_make_link, 4),
    ("reference_def", m_reference_def, 3),
    ("backslash_escape", m_backslash_escape, 3),
    ("insert_punct", m_insert_punct, 3),
    ("tricky_whitespace", m_tricky_whitespace, 2),
    ("tricky_unicode", m_tricky_unicode, 2),
    ("duplicate_fragment", m_duplicate_fragment, 2),
    ("delete_fragment", m_delete_fragment, 2),
    ("imbalance_brackets", m_imbalance_brackets, 3),
]

_WEIGHTED = [name_fn for name_fn in MUTATORS]
_NAMES = [m[0] for m in MUTATORS]
_FNS = [m[1] for m in MUTATORS]
_WEIGHTS = [m[2] for m in MUTATORS]


def mutate_once(text: str, rng: random.Random) -> tuple[str, str]:
    """Apply one weighted-random operator. Returns (operator_name, mutated)."""
    idx = rng.choices(range(len(MUTATORS)), weights=_WEIGHTS, k=1)[0]
    name, fn, _ = MUTATORS[idx]
    try:
        return name, fn(text, rng)
    except Exception:
        # An operator must never break the campaign; fall back to identity.
        return name, text
