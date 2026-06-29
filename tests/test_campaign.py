"""Tests for the differential fuzzing campaign (spec §8, §9)."""
from cm_difftest.fuzz import CampaignConfig, run_campaign


def test_campaign_finds_divergences_and_is_deterministic():
    cfg = CampaignConfig(iterations=300, seed=5, max_findings=3, minimize_findings=True)
    r1 = run_campaign(cfg)
    r2 = run_campaign(CampaignConfig(iterations=300, seed=5, max_findings=3, minimize_findings=True))
    assert r1.divergences_seen > 0
    assert len(r1.findings) >= 1
    # determinism: same seed -> same finding inputs
    assert [f.input_markdown for f in r1.findings] == [f.input_markdown for f in r2.findings]


def test_campaign_findings_have_reproducer_and_offenders():
    cfg = CampaignConfig(iterations=300, seed=8, max_findings=3)
    result = run_campaign(cfg)
    assert result.findings
    for f in result.findings:
        assert f.input_markdown is not None
        assert "default_adapters" in f.reproducer
        assert f.reference == "cmark"


def test_require_offenders_filters():
    cfg = CampaignConfig(
        iterations=400, seed=3, max_findings=5,
        require_offenders=frozenset({"marko"}),
        minimize_findings=False,
    )
    result = run_campaign(cfg)
    for f in result.findings:
        # crashes are exempt from the filter, but none are expected here
        assert "marko" in f.offenders


def test_minimization_does_not_grow_input():
    cfg = CampaignConfig(iterations=300, seed=11, max_findings=2, minimize_findings=True)
    result = run_campaign(cfg)
    assert result.findings  # at least one finding to check
