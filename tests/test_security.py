"""Tests for the Phase 3 security comparison (spec §6)."""
from cm_difftest.security import POSTURE, detect_sinks, generate_vectors, scan


def test_detect_sinks_dangerous_url():
    assert "dangerous_url" in detect_sinks('<a href="javascript:alert(1)">x</a>')
    # entity-obfuscated colon still resolves to javascript: in a browser
    assert "dangerous_url" in detect_sinks('<a href="javascript&#58;alert(1)">x</a>')
    # control char in scheme (browsers strip it)
    assert "dangerous_url" in detect_sinks('<a href="java\tscript:alert(1)">x</a>')
    assert "dangerous_url" in detect_sinks('<img src="data:text/html,x">')


def test_detect_sinks_tags_and_handlers():
    assert "dangerous_tag" in detect_sinks("<script>x</script>")
    assert "dangerous_tag" in detect_sinks("<iframe src=x>")
    assert "event_handler" in detect_sinks('<img src=x onerror="alert(1)">')


def test_detect_sinks_no_false_positive_on_safe_link():
    assert detect_sinks('<a href="https://example.com">ok</a>') == set()
    assert detect_sinks("<p>just text with javascript: in prose</p>") == set()


def test_scan_mistletoe_leaks_but_is_not_a_bypass():
    r = scan("[x](javascript:alert(1))")
    # mistletoe emits the live href...
    assert "dangerous_url" in r.sinks["mistletoe"]
    # ...but it declares no sanitizer, so it is posture, not a bypass
    assert r.bypasses["mistletoe"] == set()
    # the sanitizing parsers block it entirely
    for name in ("markdown-it-py", "marko", "cmark"):
        assert r.sinks[name] == set()
        assert r.bypasses[name] == set()
    assert not r.has_bypass


def test_posture_map_shape():
    assert POSTURE["mistletoe"] == set()
    assert "dangerous_url" in POSTURE["marko"]
    assert "dangerous_tag" in POSTURE["markdown-it-py"]
    assert "dangerous_tag" in POSTURE["cmark"]


def test_generate_vectors_yields_strings():
    vs = []
    for i, v in enumerate(generate_vectors(seed=1)):
        vs.append(v)
        if i >= 50:
            break
    assert all(isinstance(v, str) for v in vs)
    assert any("javascript" in v.lower() for v in vs)
