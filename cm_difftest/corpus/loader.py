"""Loader for the official CommonMark ``spec.txt`` corpus (spec §7.2).

``spec.txt`` interleaves prose with conformance examples. Each example is
delimited by a fence of exactly 32 backticks; the opening fence is followed by
" example", a single ``.`` line separates the Markdown input from the expected
HTML, and section headings (``#+ ``) label the surrounding examples::

    ```````````````````````````````` example
    <markdown input>
    .
    <expected html>
    ````````````````````````````````

The parsing here mirrors the official ``test/spec_tests.py`` ``get_tests``
function exactly — including the ``→`` (U+2192) -> tab substitution the spec
uses to make hard tabs visible — so the corpus we load is byte-for-byte what
the spec project tests against.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import resources

from cm_difftest import SPEC_VERSION

__all__ = ["Example", "load_spec", "default_spec_path", "SPEC_VERSION"]

_FENCE = "`" * 32
_OPEN_FENCE = _FENCE + " example"
_HEADER_RE = re.compile(r"#+ ")
# The spec renders hard tabs as a visible right-arrow; restore them.
_TAB_MARKER = "→"


@dataclass(frozen=True)
class Example:
    """A single ``(markdown, expected_html)`` conformance example."""

    markdown: str
    html: str  # expected HTML
    section: str
    number: int
    start_line: int
    end_line: int


def default_spec_path() -> str:
    """Absolute path to the packaged, pinned ``spec.txt`` (version SPEC_VERSION)."""
    res = resources.files("cm_difftest.corpus") / f"spec-{SPEC_VERSION}.txt"
    return str(res)


def load_spec(path: str | None = None) -> list[Example]:
    """Parse ``spec.txt`` into a list of :class:`Example`.

    ``path`` defaults to the packaged, pinned corpus. The return order matches
    the file order (and the spec's example numbering, 1-based).
    """
    if path is None:
        path = default_spec_path()

    examples: list[Example] = []
    line_number = 0
    start_line = 0
    example_number = 0
    markdown_lines: list[str] = []
    html_lines: list[str] = []
    state = 0  # 0 = prose, 1 = reading markdown, 2 = reading expected html
    headertext = ""

    with open(path, "r", encoding="utf-8", newline="\n") as fh:
        for line in fh:
            line_number += 1
            stripped = line.strip()
            if stripped == _OPEN_FENCE:
                state = 1
            elif stripped == _FENCE:
                state = 0
                example_number += 1
                examples.append(
                    Example(
                        markdown="".join(markdown_lines).replace(_TAB_MARKER, "\t"),
                        html="".join(html_lines).replace(_TAB_MARKER, "\t"),
                        section=headertext,
                        number=example_number,
                        start_line=start_line,
                        end_line=line_number,
                    )
                )
                start_line = 0
                markdown_lines = []
                html_lines = []
            elif state == 1:
                if stripped == ".":
                    state = 2
                else:
                    if start_line == 0:
                        start_line = line_number - 1
                    markdown_lines.append(line)
            elif state == 2:
                html_lines.append(line)
            elif state == 0 and _HEADER_RE.match(line):
                headertext = _HEADER_RE.sub("", line).strip()

    return examples
