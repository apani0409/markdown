"""Hypothesis strategies for Markdown (spec §8, third generation source).

Generates valid-ish Markdown by assembling syntactic fragments, so property
tests can assert "no parser crashes" and "all normalized outputs agree" and let
Hypothesis shrink any failure automatically.
"""
from __future__ import annotations

from hypothesis import strategies as st

__all__ = ["markdown_fragments", "markdown_documents", "inline_text"]

# Inline-ish content with a few markdown-significant characters mixed in.
# (st.text requires single-character alphabet elements.)
inline_text = st.text(
    alphabet="abc 123*_`~[]()<>&!\\#-+.\n\t\"'öé",
    min_size=0,
    max_size=20,
)


def _wrap(prefix: str, suffix: str = ""):
    return inline_text.map(lambda s: f"{prefix}{s}{suffix}")


markdown_fragments = st.one_of(
    _wrap("*", "*"),
    _wrap("**", "**"),
    _wrap("_", "_"),
    _wrap("`", "`"),
    _wrap("# "),
    _wrap("> "),
    _wrap("- "),
    _wrap("1. "),
    inline_text.map(lambda s: f"[{s}](http://x)"),
    inline_text.map(lambda s: f"![{s}](/img)"),
    inline_text.map(lambda s: f"[{s}]: /url"),
    st.sampled_from(["<div>", "</div>", "<b>x</b>", "<!-- c -->", "<script>x</script>"]),
    st.sampled_from(["&amp;", "&#42;", "&notreal;", "&#x1F600;", "\\*", "\\[", "```\ncode\n```"]),
    inline_text,
)


markdown_documents = st.lists(markdown_fragments, min_size=1, max_size=8).map("\n".join)
