"""Tests for the parser adapters (spec §7.1)."""
import pytest

from cm_difftest.adapters import (
    Adapter,
    AdapterError,
    Mode,
    default_adapters,
    get_adapter,
    reference_adapter,
    sut_adapters,
)
from cm_difftest.adapters.cmark import find_libcmark


def test_default_adapter_set_shape():
    adapters = default_adapters()
    assert [a.name for a in adapters] == ["markdown-it-py", "mistletoe", "marko", "cmark"]
    assert all(isinstance(a, Adapter) for a in adapters)
    # exactly one reference, and it is cmark, listed last
    refs = [a for a in adapters if a.is_reference]
    assert [r.name for r in refs] == ["cmark"]
    assert adapters[-1].name == "cmark"


def test_sut_and_reference_split():
    assert [a.name for a in sut_adapters()] == ["markdown-it-py", "mistletoe", "marko"]
    assert reference_adapter().name == "cmark"


@pytest.mark.parametrize("name", ["markdown-it-py", "mistletoe", "marko", "cmark"])
def test_raw_mode_basic_render(name):
    out = get_adapter(name).render("*hi* **bold**", mode=Mode.RAW)
    assert out.strip() == "<p><em>hi</em> <strong>bold</strong></p>"


@pytest.mark.parametrize("name", ["markdown-it-py", "mistletoe", "marko", "cmark"])
def test_raw_mode_passes_raw_html_through(name):
    out = get_adapter(name).render("<div>x</div>", mode=Mode.RAW)
    assert "<div>" in out and "x" in out


def test_provenance_is_populated():
    for a in default_adapters():
        p = a.provenance()
        assert p.name == a.name
        assert p.library_version
        assert p.target_spec_version
        assert p.is_reference == a.is_reference


def test_cmark_reference_version_matches_pin():
    p = reference_adapter().provenance()
    assert p.library_version == "0.31.2"
    assert p.is_reference is True


def test_cmark_safe_mode_scrubs_raw_html():
    cmark = get_adapter("cmark")
    safe = cmark.render("<script>alert(1)</script>", mode=Mode.SAFE)
    assert "<script>" not in safe
    raw = cmark.render("<script>alert(1)</script>", mode=Mode.RAW)
    assert "<script>" in raw


def test_markdownit_safe_mode_escapes_raw_html():
    out = get_adapter("markdown-it-py").render("<b>x</b>", mode=Mode.SAFE)
    assert "&lt;b&gt;" in out and "<b>" not in out


@pytest.mark.parametrize("name", ["mistletoe", "marko"])
def test_single_mode_parsers_render_in_both_modes(name):
    # marko and mistletoe have one rendering mode; SAFE must not raise (their
    # security posture is recorded by the Phase 3 comparison, not by erroring).
    out = get_adapter(name).render("<b>x</b>", mode=Mode.SAFE)
    assert isinstance(out, str) and "x" in out


def test_get_adapter_unknown_raises():
    with pytest.raises(AdapterError):
        get_adapter("not-a-parser")


def test_find_libcmark_returns_existing_path():
    import os

    path = find_libcmark()
    assert os.path.exists(path)
    assert "libcmark" in path
