"""M1 done-criterion verification over the full spec.txt corpus (spec §10, M1).

This is the automated gate for Milestone 1: running the whole corpus must yield
zero false-positive divergences attributable to normalization. We prove that
two ways:

* the reference (cmark 0.31.2) matches spec.txt on every example, and
* two further independent implementations (markdown-it-py, marko) also reach
  100% — impossible if the normalizer were collapsing real differences or
  failing to collapse formatting noise.

The exact pass counts are tied to the pinned library versions (requirements.lock).
"""
from cm_difftest.report.scorecard import build_scorecard
from cm_difftest.corpus import load_spec
from cm_difftest.runner import DifferentialRunner


def test_full_corpus_m1_criterion():
    examples = load_spec()
    card = build_scorecard(examples, DifferentialRunner(timeout_s=15))

    assert card.total == 652

    # --- M1 done-criterion: zero normalization false positives ---
    assert card.reference_fidelity() == (652, 652), "cmark must match spec.txt exactly"
    assert card.normalization_artifacts() == 0

    totals = card.totals()
    # Independent 100%s corroborate that normalization adds no false positives.
    assert totals["cmark"] == 652
    assert totals["markdown-it-py"] == 652
    assert totals["marko"] == 652

    # mistletoe 1.5.1 has genuine, recorded compliance gaps (version-specific).
    assert totals["mistletoe"] == 628


def test_every_example_runs_without_crashing():
    """No SUT or the reference may crash on any spec.txt example (spec §3)."""
    runner = DifferentialRunner(timeout_s=15)
    for ex in load_spec():
        comp = runner.run(ex.markdown, expected_html=ex.html)
        assert not comp.has_failure(), (
            f"a parser crashed on spec example #{ex.number} ({ex.section})"
        )
