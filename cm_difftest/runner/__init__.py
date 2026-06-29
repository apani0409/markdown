"""Runner subpackage: differential runner with guards (spec §7.4)."""

from cm_difftest.runner.differential import DifferentialRunner
from cm_difftest.runner.guard import (
    guarded_render,
    guarded_render_isolated,
    TimeoutExceeded,
)
from cm_difftest.runner.result import Comparison, RenderResult, Status

__all__ = [
    "DifferentialRunner",
    "Comparison",
    "RenderResult",
    "Status",
    "guarded_render",
    "guarded_render_isolated",
    "TimeoutExceeded",
]
