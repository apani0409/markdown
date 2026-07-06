"""Tests for the scorecard + findings reporters (spec §7.8)."""
import json

from cm_difftest.corpus import Example
from cm_difftest.report import scorecard as sc
from cm_difftest.report import findings as fnd
from cm_difftest.runner import DifferentialRunner
from cm_difftest.runner.result import Comparison, RenderResult, Status
from cm_difftest.triage import classify


def _examples():
    # inputs every compliant parser handles identically
    return [
        Example("*hi*", "<p><em>hi</em></p>\n", "Emphasis", 1, 1, 2),
        Example("# Title", "<h1>Title</h1>\n", "ATX headings", 2, 3, 4),
        Example("a\n", "<p>a</p>\n", "Paragraphs", 3, 5, 6),
    ]


def test_build_scorecard_all_pass():
    card = sc.build_scorecard(_examples(), DifferentialRunner(timeout_s=10), generated="2026-06-29")
    assert card.total == 3
    totals = card.totals()
    for name in ("markdown-it-py", "mistletoe", "marko", "cmark"):
        assert totals[name] == 3
    # reference fidelity == total -> zero normalizer false positives
    assert card.reference_fidelity() == (3, 3)
    assert card.normalization_artifacts() == 0


def test_scorecard_json_roundtrip():
    card = sc.build_scorecard(_examples(), DifferentialRunner(timeout_s=10))
    d = sc.to_dict(card)
    s = json.dumps(d)  # must be JSON-serializable
    d2 = json.loads(s)
    assert d2["summary"]["total_examples"] == 3
    assert set(d2["sut_names"]) == {"markdown-it-py", "mistletoe", "marko"}
    assert d2["reference_name"] == "cmark"


def test_scorecard_markdown_has_sections(tmp_path):
    card = sc.build_scorecard(_examples(), DifferentialRunner(timeout_s=10), generated="2026-06-29")
    p = tmp_path / "scorecard.md"
    sc.write_markdown(card, str(p))
    text = p.read_text(encoding="utf-8")
    assert "# CommonMark compliance scorecard" in text
    assert "## Provenance" in text
    assert "## Overall" in text
    assert "M1 done-criterion" in text
    assert "## By section" in text


def test_scorecard_by_section_counts():
    card = sc.build_scorecard(_examples(), DifferentialRunner(timeout_s=10))
    by_sec = card.by_section()
    assert by_sec["Emphasis"]["cmark"] == (1, 1)
    assert set(by_sec) == {"Emphasis", "ATX headings", "Paragraphs"}


def test_findings_writer(tmp_path):
    comp = Comparison(
        "md", "raw",
        [
            RenderResult("markdown-it-py", Status.OK, html="<p>x</p>", normalized="<p>x</p>"),
            RenderResult("cmark", Status.OK, html="<p>y</p>", normalized="<p>y</p>"),
        ],
        reference="cmark",
    )
    cls = classify(comp)
    finding = fnd.make_finding("F-001", comp, cls)
    assert finding.id == "F-001"
    assert "default_adapters" in finding.reproducer

    jpath = tmp_path / "findings.json"
    mpath = tmp_path / "findings.md"
    fnd.write_json([finding], str(jpath))
    fnd.write_markdown([finding], str(mpath))
    data = json.loads(jpath.read_text(encoding="utf-8"))
    assert data[0]["id"] == "F-001"
    assert "F-001" in mpath.read_text(encoding="utf-8")
