"""Regression characterization of M2 differential findings (spec §8, §9).

Each case is a genuine divergence the fuzzer surfaced *beyond* the static
corpus, where the cmark 0.31.2 reference agrees with the spec and at least one
other implementation, and a named offender disagrees. These tests pin the
*current* behavior of the pinned library versions (requirements.lock): if an
upstream release fixes one, the corresponding test flips — which is exactly the
signal we want.

They double as the machine-checkable record that M2's done-criterion is met:
≥1 genuine, minimized divergence with an identified likely-wrong implementation.
"""
import pytest

from cm_difftest.normalize import normalize_html
from cm_difftest.runner import DifferentialRunner

# (id, input, spec-correct HTML (== cmark), offenders that disagree)
CASES = [
    # marko: a lone bullet/ordered marker at EOF (no trailing newline) is parsed
    # as a paragraph instead of an empty list item. Trailing-newline family.
    ("marko-lone-star", "*", "<ul>\n<li></li>\n</ul>\n", {"marko"}),
    ("marko-lone-dash", "-", "<ul>\n<li></li>\n</ul>\n", {"marko"}),
    ("marko-lone-ordered", "1.", "<ol>\n<li></li>\n</ol>\n", {"marko"}),
    # marko: "<!" is treated as a raw HTML block instead of being escaped as text
    # ("<!" is not a valid HTML-block start condition).
    ("marko-bang-htmlblock", "<!", "<p>&lt;!</p>\n", {"marko"}),
    # marko: over-percent-encodes the URL sub-delimiter ";" (-> %3B).
    ("marko-url-semicolon", "[](;)", '<p><a href=";"></a></p>\n', {"marko"}),
    # markdown-it-py: fails to recognize a code span in this context.
    ("markdownit-codespan", "[`t`>`", "<p>[<code>t</code>&gt;`</p>\n", {"markdown-it-py"}),
    # marko + mistletoe: treat "-<NBSP>--" as a thematic break; a non-breaking
    # space is not a valid thematic-break space, so it must stay a paragraph.
    ("nbsp-thematic-break", "-\xa0--", "<p>-\xa0--</p>\n", {"marko", "mistletoe"}),
]


# Crash-class finding (spec §3): mistletoe raises on certain emphasis runs while
# every other implementation renders it. Found by the Atheris target, minimized
# with ddmin. Root cause: mistletoe/core_tokens.py process_emphasis ->
# closer.type[0] with an empty closer.type.
MISTLETOE_CRASH_INPUT = '****"************+****'


def test_mistletoe_crash_reproduces():
    import mistletoe

    with pytest.raises(IndexError):
        mistletoe.markdown(MISTLETOE_CRASH_INPUT)

    # the other implementations must NOT crash on the same input
    from cm_difftest.adapters import get_adapter, Mode

    for name in ("markdown-it-py", "marko", "cmark"):
        out = get_adapter(name).render(MISTLETOE_CRASH_INPUT, mode=Mode.RAW)
        assert isinstance(out, str) and out


def test_runner_guards_the_mistletoe_crash():
    """The harness must capture the crash, not die with the parser (spec §3)."""
    from cm_difftest.runner import DifferentialRunner
    from cm_difftest.runner.result import Status

    comp = DifferentialRunner(timeout_s=10).run(MISTLETOE_CRASH_INPUT)
    assert comp.has_failure()
    mistletoe_result = comp.by_name("mistletoe")
    assert mistletoe_result.status is Status.EXCEPTION
    assert mistletoe_result.error_type == "IndexError"


@pytest.mark.parametrize("case_id,md,correct,offenders", CASES, ids=[c[0] for c in CASES])
def test_finding_reproduces(case_id, md, correct, offenders):
    runner = DifferentialRunner(timeout_s=10)
    comp = runner.run(md)
    want = normalize_html(correct)

    # The reference matches the spec-correct output.
    cmark = comp.by_name("cmark")
    assert cmark.ok and cmark.normalized == want, (
        f"{case_id}: cmark != expected\n got {cmark.normalized!r}\n want {want!r}"
    )

    # It is a genuine divergence with exactly the expected offenders.
    assert comp.has_divergence()
    actual_offenders = {
        r.adapter for r in comp.results
        if r.adapter != "cmark" and (not r.ok or r.normalized != want)
    }
    assert actual_offenders == offenders, (
        f"{case_id}: offenders {actual_offenders} != expected {offenders}"
    )
