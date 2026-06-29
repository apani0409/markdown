"""cm-difftest — differential conformance + fuzzing harness for Python CommonMark parsers.

The package is organised by single-responsibility components (spec §7):

    normalize/  the ported official ``normalize_html`` (the safety-critical unit)
    corpus/     spec.txt loader -> Example(markdown, expected_html, section, number)
    adapters/   one uniform ``render(markdown, *, mode)`` wrapper per parser + cmark
    runner/     differential runner with timeout / exception / memory guards
    report/     compliance scorecard + findings writers (JSON + Markdown)

Build strictly in milestone order (spec §10). Milestone 1 = harness + scorecard
with zero normalization false positives before any fuzzing is written.
"""

__version__ = "0.1.0"

# The single pinned CommonMark spec version this harness aligns to (spec §5).
SPEC_VERSION = "0.31.2"
