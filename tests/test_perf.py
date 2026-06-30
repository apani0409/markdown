"""Tests for the performance / complexity comparison (spec §3 DoS class)."""
import pytest

from cm_difftest.adapters import get_adapter
from cm_difftest.perf import FAMILIES, growth_exponent, measure


def test_growth_exponent_recovers_quadratic():
    # times scale as size**2 -> exponent ~2.0
    sizes = [10, 100, 1000]
    times = [1e-3, 1e-1, 1e1]
    exp = growth_exponent(sizes, times)
    assert exp is not None and abs(exp - 2.0) < 0.05


def test_growth_exponent_linear():
    sizes = [10, 100, 1000]
    times = [1e-4, 1e-3, 1e-2]
    exp = growth_exponent(sizes, times)
    assert exp is not None and abs(exp - 1.0) < 0.05


def test_measure_ok_on_small_input():
    status, secs = measure(get_adapter("cmark"), "*hi*", budget=5.0)
    assert status == "ok" and secs >= 0


@pytest.mark.parametrize("name", ["mistletoe", "marko"])
def test_deep_blockquote_recurses(name):
    # ~600 nested '>' overflows the Python stack in these parsers (DoS finding)
    status, _ = measure(get_adapter(name), ">" * 600 + " x", budget=10.0)
    assert status == "recursion"


@pytest.mark.parametrize("name", ["markdown-it-py", "cmark"])
def test_deep_blockquote_robust(name):
    # markdown-it-py (maxNesting) and cmark (iterative) handle the same input
    status, _ = measure(get_adapter(name), ">" * 600 + " x", budget=10.0)
    assert status == "ok"


def test_fuzz_amplifiers_runs_and_flags_only_offenders():
    from cm_difftest.perf import fuzz_amplifiers

    hits = fuzz_amplifiers(seed=0, n_fragments=40, reps=(500, 1000, 2000), budget=4.0)
    assert isinstance(hits, list)
    # the reference is never reported as an offender against itself
    assert all(h["parser"] != "cmark" for h in hits)
    assert all(set(h) >= {"parser", "fragment", "kind"} for h in hits)


def test_families_are_linear_length():
    # every family's input length must be ~linear in n (fair complexity probe)
    for name, mk in FAMILIES.items():
        small, big = len(mk(100)), len(mk(1000))
        assert big < small * 20, f"family {name} grows super-linearly in length"
