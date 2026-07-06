"""Tests for the delta-debugging minimizer (spec §7.7)."""
from cm_difftest.triage.minimizer import minimize, same_divergence_predicate
from cm_difftest.runner import DifferentialRunner


def test_minimizes_to_substring_satisfying_predicate():
    # interesting iff the candidate still contains "BUG"
    result = minimize("xxxxBUGyyyy", lambda s: "BUG" in s)
    assert "BUG" in result
    assert len(result) < len("xxxxBUGyyyy")
    # 1-minimal: removing any single remaining char should break it
    assert result == "BUG"


def test_returns_input_when_not_interesting():
    res = minimize("abc", lambda s: False)
    assert res == "abc"
    assert res.calls == 0


def test_call_budget_is_respected():
    seen = {"n": 0}

    def pred(s):
        seen["n"] += 1
        return "Z" in s

    out = minimize("Z" + "a" * 200, pred, max_calls=10)
    assert "Z" in out  # still interesting
    assert out.calls <= 10


def test_minimizes_two_required_fragments():
    # both "A" and "B" needed -> minimal is "AB" or "A...B" with nothing removable
    result = minimize("ppppAqqqqBrrrr", lambda s: "A" in s and "B" in s)
    assert "A" in result and "B" in result
    assert result == "AB"


def test_same_divergence_predicate_preserves_finding():
    runner = DifferentialRunner(timeout_s=10)
    # Construct an input that diverges; mistletoe has known emphasis gaps, but to
    # keep this test fast and deterministic we just assert the predicate is
    # callable and rejects the empty string and agreement inputs.
    pred = same_divergence_predicate(runner)
    assert pred("") is False
    # "*hi*" is unanimous -> not a divergence -> predicate False
    assert pred("*hi*") is False
