"""Atheris (libFuzzer) coverage-guided crash target (spec §8).

Run manually for the crash class:

    python -m cm_difftest.fuzz.atheris_target -atype=... <corpus_dir>

Atheris instruments the pure-Python SUTs and drives them with coverage feedback.
We keep the *differential* signal as the primary goal (see campaign.py); crash
fuzzing is a bonus — hardened parsers often yield zero crashes (spec §8). The
target renders the input through every SUT under the in-process guard; an
uncaught parser failure that the guard classifies as a crash raises so libFuzzer
records it.

Importing this module does not require atheris; only ``main`` does.
"""
from __future__ import annotations

import sys


def _consume(data: bytes) -> str:
    # Markdown is Unicode text; map arbitrary fuzzer bytes to a valid str so the
    # decode step never raises (that would be a harness bug, not a parser bug).
    return data.decode("utf-8", errors="replace")


def make_test_one_input():
    from cm_difftest.adapters import sut_adapters
    from cm_difftest.runner.guard import guarded_render
    from cm_difftest.runner.result import Status

    adapters = sut_adapters()

    def test_one_input(data: bytes) -> None:
        text = _consume(data)
        for adapter in adapters:
            result = guarded_render(adapter, text, timeout_s=5.0)
            # EXCEPTION/MEMORY/TIMEOUT on a parser of untrusted input is a finding.
            if result.status in (Status.EXCEPTION, Status.MEMORY):
                raise RuntimeError(
                    f"{adapter.name} failed: {result.error}\ninput={text!r}"
                )

    return test_one_input


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - needs atheris runtime
    import atheris

    argv = list(argv if argv is not None else sys.argv)
    test_one_input = make_test_one_input()
    atheris.Setup(argv, test_one_input)
    atheris.Fuzz()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
