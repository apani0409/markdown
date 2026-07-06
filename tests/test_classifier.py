"""Tests for the triage classifier (spec §7.5)."""
from cm_difftest.adapters.base import Provenance
from cm_difftest.runner.result import Comparison, RenderResult, Status
from cm_difftest.triage import Category, classify

PROV = [
    Provenance("markdown-it-py", "4.2.0", "0.31.2"),
    Provenance("mistletoe", "1.5.1", "not declared"),
    Provenance("marko", "2.2.3", "0.31.2"),
    Provenance("cmark", "0.31.2", "0.31.2", is_reference=True),
]


def _ok(name, normalized, html=None):
    return RenderResult(name, Status.OK, html=html if html is not None else normalized,
                        normalized=normalized)


def _fail(name, status=Status.EXCEPTION, error_type="ValueError", error="ValueError: boom"):
    return RenderResult(name, status, error=error, error_type=error_type)


def test_agreement_static():
    comp = Comparison(
        "md", "raw",
        [_ok("markdown-it-py", "<p>x</p>"), _ok("cmark", "<p>x</p>")],
        expected_html="<p>x</p>", expected_normalized="<p>x</p>", reference="cmark",
    )
    c = classify(comp, PROV)
    assert c.category is Category.AGREEMENT


def test_spec_noncompliance_with_version_skew_flag():
    # only mistletoe (target "not declared") disagrees -> skew is *possible*
    comp = Comparison(
        "md", "raw",
        [
            _ok("markdown-it-py", "<p>x</p>"),
            _ok("mistletoe", "<p>WRONG</p>"),
            _ok("marko", "<p>x</p>"),
            _ok("cmark", "<p>x</p>"),
        ],
        expected_html="<p>x</p>", expected_normalized="<p>x</p>", reference="cmark",
    )
    c = classify(comp, PROV)
    assert c.category is Category.SPEC_NONCOMPLIANCE
    assert c.offenders == ["mistletoe"]
    assert "possible_version_skew" in c.flags


def test_spec_noncompliance_no_skew_when_baseline_parser_offends():
    # marko targets 0.31.2; if it offends, this is not version skew
    comp = Comparison(
        "md", "raw",
        [_ok("marko", "<p>WRONG</p>"), _ok("cmark", "<p>x</p>")],
        expected_html="<p>x</p>", expected_normalized="<p>x</p>", reference="cmark",
    )
    c = classify(comp, PROV)
    assert c.category is Category.SPEC_NONCOMPLIANCE
    assert "possible_version_skew" not in c.flags


def test_crash_category_takes_priority():
    comp = Comparison(
        "md", "raw",
        [_ok("markdown-it-py", "<p>x</p>"), _fail("mistletoe")],
        expected_html="<p>x</p>", expected_normalized="<p>x</p>", reference="cmark",
    )
    c = classify(comp, PROV)
    assert c.category is Category.CRASH
    assert c.offenders == ["mistletoe"]


def test_inter_parser_disagreement_dynamic_uses_reference():
    comp = Comparison(
        "md", "raw",
        [
            _ok("markdown-it-py", "<p>x</p>"),
            _ok("mistletoe", "<p>y</p>"),
            _ok("cmark", "<p>x</p>"),
        ],
        reference="cmark",
    )
    c = classify(comp, PROV)
    assert c.category is Category.INTER_PARSER_DISAGREEMENT
    assert c.offenders == ["mistletoe"]


def test_security_flag_on_sink_disagreement():
    comp = Comparison(
        "md", "raw",
        [
            _ok("markdown-it-py", '<p><a href="">a</a></p>', html='<p><a href="">a</a></p>'),
            _ok("cmark", '<p><a href="javascript:x">a</a></p>',
                html='<p><a href="javascript:x">a</a></p>'),
        ],
        reference="cmark",
    )
    c = classify(comp, PROV)
    assert "possible_security_candidate" in c.flags
