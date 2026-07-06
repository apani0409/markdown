"""Tests for the spec.txt corpus loader (spec §7.2)."""
from cm_difftest.corpus import Example, load_spec, default_spec_path, SPEC_VERSION


def test_loads_expected_example_count():
    examples = load_spec()
    # CommonMark 0.31.2 ships 652 conformance examples.
    assert len(examples) == 652


def test_default_spec_path_matches_pinned_version():
    assert default_spec_path().endswith(f"spec-{SPEC_VERSION}.txt")
    assert SPEC_VERSION == "0.31.2"


def test_example_numbering_is_sequential_and_1_based():
    examples = load_spec()
    assert [e.number for e in examples] == list(range(1, len(examples) + 1))


def test_first_example_is_the_tabs_case_with_tabs_restored():
    e1 = load_spec()[0]
    assert isinstance(e1, Example)
    assert e1.section == "Tabs"
    # the arrow markers must be turned back into real tab characters
    assert e1.markdown == "\tfoo\tbaz\t\tbim\n"
    assert e1.html == "<pre><code>foo\tbaz\t\tbim\n</code></pre>\n"


def test_no_arrow_markers_survive_substitution():
    for e in load_spec():
        assert "→" not in e.markdown, f"arrow left in markdown of #{e.number}"
        assert "→" not in e.html, f"arrow left in html of #{e.number}"


def test_every_example_has_section_and_line_span():
    for e in load_spec():
        assert e.section, f"example #{e.number} has no section"
        assert e.start_line > 0 and e.end_line > e.start_line, (
            f"example #{e.number} has a bad line span: {e.start_line}..{e.end_line}"
        )


def test_known_sections_present():
    sections = {e.section for e in load_spec()}
    for expected in (
        "Tabs",
        "ATX headings",
        "Fenced code blocks",
        "Links",
        "Emphasis and strong emphasis",
        "Raw HTML",
    ):
        assert expected in sections, f"missing section: {expected}"


def test_markdown_and_html_are_strings():
    for e in load_spec():
        assert isinstance(e.markdown, str)
        assert isinstance(e.html, str)
