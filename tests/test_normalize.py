"""Tests for the ported official HTML normalizer (spec §4).

The normalizer is the single most safety-critical unit: the whole M1
done-criterion is "zero false-positive divergences attributable to
normalization". We test it three ways:

1. the official doctests (ported verbatim) still pass;
2. hand-picked tricky pairs that *must* normalize equal (the noise sources
   §4 calls out: whitespace between block tags, attribute order/quoting,
   entity encoding, void-element spelling);
3. genuinely different HTML that *must* stay distinct (so the normalizer is
   not over-collapsing and hiding real divergences).
"""
import doctest

import pytest

from cm_difftest.normalize import normalize_html
import cm_difftest.normalize.html as normalize_module


def test_official_doctests_pass():
    """The doctests ported from the official normalize.py must all pass."""
    results = doctest.testmod(normalize_module, verbose=False)
    assert results.attempted > 0, "no doctests were collected"
    assert results.failed == 0, f"{results.failed} doctest(s) failed"


# --- Pairs that MUST normalize to the same string (insignificant differences) ---
EQUAL_PAIRS = [
    # insignificant inner whitespace
    ("<p>a  b</p>", "<p>a b</p>"),
    ("<p>a  \t b</p>", "<p>a b</p>"),
    # whitespace surrounding block-level tags
    ("\n\t<p>\n\t\ta  b\t\t</p>\n\t", "<p>a b</p>"),
    ("<p>foo</p>\n", "<p>foo</p>"),
    ("<ul>\n<li>a</li>\n<li>b</li>\n</ul>", "<ul><li>a</li><li>b</li></ul>"),
    # void / self-closing element spelling
    ("<br />", "<br>"),
    ("<hr/>", "<hr>"),
    ("<img src='x' alt='y' />", '<img alt="y" src="x">'),
    # attribute order and quoting style
    ('<a href="foo" title="bar">x</a>', "<a title='bar' href='foo'>x</a>"),
    ('<a HREF="foo">x</a>', '<a href="foo">x</a>'),
    # entity vs numeric char reference vs literal unicode
    ("&amp;", "&#38;"),
    ("&forall;", "∀"),
    ("&#x2200;", "&forall;"),
    # angle-bracket / ampersand entities are canonicalised the same way
    ("&lt;&gt;&amp;&quot;", "&#60;&#62;&#38;&#34;"),
]


@pytest.mark.parametrize("a,b", EQUAL_PAIRS)
def test_insignificant_differences_normalize_equal(a, b):
    assert normalize_html(a) == normalize_html(b), (
        f"expected equal after normalization:\n  {a!r}\n  {b!r}\n"
        f"got:\n  {normalize_html(a)!r}\n  {normalize_html(b)!r}"
    )


# --- Pairs that MUST stay distinct (genuine, significant differences) ---
DISTINCT_PAIRS = [
    ("<p>a</p>", "<p>b</p>"),
    ("<em>x</em>", "<strong>x</strong>"),
    ('<a href="a">x</a>', '<a href="b">x</a>'),
    # <pre> preserves internal whitespace, so these are genuinely different
    ("<pre>a  b</pre>", "<pre>a b</pre>"),
    ("<pre><code>a  b</code></pre>", "<pre><code>a b</code></pre>"),
    # different nesting is a real divergence
    ("<p><em>x</em></p>", "<em><p>x</p></em>"),
]


@pytest.mark.parametrize("a,b", DISTINCT_PAIRS)
def test_significant_differences_stay_distinct(a, b):
    assert normalize_html(a) != normalize_html(b), (
        f"normalizer over-collapsed a real difference:\n  {a!r}\n  {b!r}"
    )


def test_pre_preserves_internal_whitespace():
    out = normalize_html("<pre>a  \t b</pre>")
    assert "a  \t b" in out, f"<pre> whitespace was collapsed: {out!r}"


IDEMPOTENT_INPUTS = [
    "<p>a  b</p>\n",
    "<br />",
    '<a href="foo" title="bar">x</a>',
    "&forall;&amp;&gt;&lt;&quot;",
    "<pre>a  b</pre>",
    "<ul>\n<li>x</li>\n</ul>",
    "<blockquote>\n<p>q</p>\n</blockquote>",
]


@pytest.mark.parametrize("html_in", IDEMPOTENT_INPUTS)
def test_normalization_is_idempotent(html_in):
    once = normalize_html(html_in)
    twice = normalize_html(once)
    assert once == twice, f"not idempotent:\n  {once!r}\n  {twice!r}"


def test_comment_and_cdata_preserved():
    assert normalize_html("<!-- hi -->") == "<!-- hi -->"
    # CDATA chunks are passed through verbatim by the chunking workaround
    assert "<![CDATA[ x<y ]]>" in normalize_html("<p><![CDATA[ x<y ]]></p>")
