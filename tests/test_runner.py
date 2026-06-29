"""Tests for the differential runner: result logic, guards, isolation (spec §7.4)."""
import time

import pytest

from cm_difftest.adapters.base import Adapter, Mode, Provenance
from cm_difftest.runner import (
    Comparison,
    DifferentialRunner,
    RenderResult,
    Status,
    guarded_render,
    guarded_render_isolated,
)


# --------------------------------------------------------------------------- #
# Stub adapters (deterministic failure modes)
# --------------------------------------------------------------------------- #
class _Stub(Adapter):
    name = "stub"

    def __init__(self, name, fn):
        self.name = name
        self._fn = fn

    def render(self, markdown, *, mode=Mode.RAW):
        return self._fn(markdown)

    def provenance(self):
        return Provenance(self.name, "0", "0")


def _ok(out):
    return _Stub(out, lambda md: out)  # name == output, for easy grouping


def _raise(exc):
    def fn(md):
        raise exc

    return _Stub("raiser", fn)


def _sleep(seconds):
    return _Stub("sleeper", lambda md: time.sleep(seconds) or "<p>late</p>")


def _recurse():
    def fn(md):
        def deep(n):
            return deep(n + 1)

        return deep(0)

    return _Stub("recurser", fn)


# --------------------------------------------------------------------------- #
# RenderResult / Comparison logic
# --------------------------------------------------------------------------- #
def _r(name, status=Status.OK, normalized=None, error_type=None):
    return RenderResult(name, status, html=normalized, normalized=normalized, error_type=error_type)


def test_unanimous_agreement_has_no_divergence():
    c = Comparison(
        "md", "raw",
        [_r("a", normalized="<p>x</p>"), _r("b", normalized="<p>x</p>")],
    )
    assert not c.has_divergence()
    assert not c.has_failure()
    assert c.agreement_groups() == [["a", "b"]]


def test_distinct_outputs_diverge():
    c = Comparison(
        "md", "raw",
        [_r("a", normalized="<p>x</p>"), _r("b", normalized="<p>y</p>")],
    )
    assert c.has_divergence()
    assert sorted(g for grp in c.agreement_groups() for g in grp) == ["a", "b"]
    assert len(c.agreement_groups()) == 2


def test_failure_diverges_from_success_and_flags_failure():
    c = Comparison(
        "md", "raw",
        [_r("a", normalized="<p>x</p>"), _r("b", status=Status.EXCEPTION, error_type="ValueError")],
    )
    assert c.has_divergence()
    assert c.has_failure()


def test_identical_failures_agree():
    c = Comparison(
        "md", "raw",
        [
            _r("a", status=Status.EXCEPTION, error_type="ValueError"),
            _r("b", status=Status.EXCEPTION, error_type="ValueError"),
        ],
    )
    assert not c.has_divergence()  # same failure -> one group
    assert c.has_failure()


def test_reference_disagreements_use_cmark_as_tiebreaker():
    c = Comparison(
        "md", "raw",
        [
            _r("markdown-it-py", normalized="<p>x</p>"),
            _r("mistletoe", normalized="<p>WRONG</p>"),
            _r("cmark", normalized="<p>x</p>"),
        ],
        reference="cmark",
    )
    assert c.reference_disagreements() == ["mistletoe"]


def test_matches_expected_static_regime():
    c = Comparison(
        "md", "raw",
        [_r("a", normalized="<p>x</p>")],
        expected_html="<p>x</p>",
        expected_normalized="<p>x</p>",
    )
    assert c.matches_expected("a") is True
    c2 = Comparison(
        "md", "raw",
        [_r("a", normalized="<p>y</p>")],
        expected_html="<p>x</p>",
        expected_normalized="<p>x</p>",
    )
    assert c2.matches_expected("a") is False


# --------------------------------------------------------------------------- #
# In-process guard
# --------------------------------------------------------------------------- #
def test_guard_ok():
    res = guarded_render(_ok("<p>hi</p>"), "x")
    assert res.ok and res.html == "<p>hi</p>"


def test_guard_captures_exception():
    res = guarded_render(_raise(ValueError("boom")), "x")
    assert res.status is Status.EXCEPTION
    assert res.error_type == "ValueError"
    assert "boom" in res.error


def test_guard_enforces_timeout():
    res = guarded_render(_sleep(3), "x", timeout_s=0.3)
    assert res.status is Status.TIMEOUT


def test_guard_captures_recursion_as_exception():
    res = guarded_render(_recurse(), "x")
    assert res.status is Status.EXCEPTION
    assert res.error_type == "RecursionError"


def test_guard_captures_memory_error():
    res = guarded_render(_raise(MemoryError()), "x")
    assert res.status is Status.MEMORY


# --------------------------------------------------------------------------- #
# Process isolation (crash class, spec §3)
# --------------------------------------------------------------------------- #
@pytest.fixture
def crash_adapters(monkeypatch):
    """Register stub adapters reachable by name in forked children."""
    import cm_difftest.adapters as adapters_pkg

    class _Segfault(Adapter):
        name = "segfaulter"

        def render(self, markdown, *, mode=Mode.RAW):
            import ctypes

            ctypes.string_at(0)  # dereference NULL -> SIGSEGV

        def provenance(self):
            return Provenance(self.name, "0", "0")

    class _Slow(Adapter):
        name = "slowpoke"

        def render(self, markdown, *, mode=Mode.RAW):
            import time as _t

            _t.sleep(10)
            return "<p>never</p>"

        def provenance(self):
            return Provenance(self.name, "0", "0")

    registry = dict(adapters_pkg.ADAPTER_CLASSES)
    registry.update({"segfaulter": _Segfault, "slowpoke": _Slow})
    monkeypatch.setattr(adapters_pkg, "ADAPTER_CLASSES", registry)
    return registry


def test_isolated_ok_with_real_adapter():
    res = guarded_render_isolated("markdown-it-py", "*hi*", timeout_s=10)
    assert res.ok
    assert "<em>hi</em>" in res.html


def test_isolated_segfault_becomes_crash(crash_adapters):
    res = guarded_render_isolated("segfaulter", "x", timeout_s=10)
    assert res.status is Status.CRASH


def test_isolated_timeout(crash_adapters):
    res = guarded_render_isolated("slowpoke", "x", timeout_s=0.5)
    assert res.status is Status.TIMEOUT


# --------------------------------------------------------------------------- #
# DifferentialRunner over real adapters
# --------------------------------------------------------------------------- #
def test_runner_unanimous_on_simple_input():
    runner = DifferentialRunner(timeout_s=10)
    comp = runner.run("*hi*", expected_html="<p><em>hi</em></p>\n")
    assert not comp.has_divergence()
    assert not comp.has_failure()
    assert comp.reference == "cmark"
    assert comp.reference_disagreements() == []
    for a in ("markdown-it-py", "mistletoe", "marko", "cmark"):
        assert comp.matches_expected(a) is True


def test_runner_normalizes_outputs():
    runner = DifferentialRunner(timeout_s=10)
    comp = runner.run("# Title")
    for r in comp.results:
        assert r.ok
        assert r.normalized is not None
