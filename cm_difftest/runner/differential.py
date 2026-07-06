"""The differential runner (spec §7.4).

Given one input, run every adapter under guards, normalize the OK outputs, and
emit a :class:`Comparison` (raw + normalized output per impl, expected if known,
and the agreement matrix).
"""
from __future__ import annotations

from dataclasses import replace

from cm_difftest.adapters import Adapter, Mode, Provenance, default_adapters
from cm_difftest.normalize import normalize_html
from cm_difftest.runner.guard import guarded_render, guarded_render_isolated
from cm_difftest.runner.result import Comparison

__all__ = ["DifferentialRunner"]


class DifferentialRunner:
    """Run a set of adapters over inputs and produce :class:`Comparison` objects.

    Parameters
    ----------
    adapters:
        Adapters to compare; defaults to the three SUTs + cmark reference.
    mode:
        RAW (default, matches spec.txt) or SAFE (Phase 3).
    timeout_s:
        Per-input time limit.
    isolated:
        If True, render each parse in a subprocess (crash/OOM-safe, slower).
    memory_mb:
        Address-space cap applied under isolation.
    """

    def __init__(
        self,
        adapters: list[Adapter] | None = None,
        *,
        mode: Mode = Mode.RAW,
        timeout_s: float = 5.0,
        isolated: bool = False,
        memory_mb: int | None = 1024,
    ) -> None:
        self.adapters = adapters if adapters is not None else default_adapters()
        self.mode = mode
        self.timeout_s = timeout_s
        self.isolated = isolated
        self.memory_mb = memory_mb
        self._reference = next((a.name for a in self.adapters if a.is_reference), None)

    @property
    def reference(self) -> str | None:
        return self._reference

    def provenance(self) -> list[Provenance]:
        return [a.provenance() for a in self.adapters]

    def run(self, markdown: str, *, expected_html: str | None = None) -> Comparison:
        results = []
        for adapter in self.adapters:
            if self.isolated:
                result = guarded_render_isolated(
                    adapter.name, markdown,
                    mode=self.mode, timeout_s=self.timeout_s, memory_mb=self.memory_mb,
                )
            else:
                result = guarded_render(
                    adapter, markdown, mode=self.mode, timeout_s=self.timeout_s
                )
            if result.ok and result.html is not None:
                result = replace(result, normalized=normalize_html(result.html))
            results.append(result)

        expected_normalized = (
            normalize_html(expected_html) if expected_html is not None else None
        )
        return Comparison(
            markdown=markdown,
            mode=self.mode.value,
            results=results,
            expected_html=expected_html,
            expected_normalized=expected_normalized,
            reference=self._reference,
        )
