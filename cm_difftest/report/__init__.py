"""Report subpackage: scorecard + findings writers (spec §7.8)."""

from cm_difftest.report import findings, scorecard
from cm_difftest.report.scorecard import (
    Scorecard,
    build_scorecard,
    to_dict,
    write_json,
    write_markdown,
)

__all__ = [
    "scorecard",
    "findings",
    "Scorecard",
    "build_scorecard",
    "to_dict",
    "write_json",
    "write_markdown",
]
