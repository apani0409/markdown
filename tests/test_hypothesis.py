"""Property-based crash test via Hypothesis (spec §8 crash class).

Asserts the invariant that matters for safety: no parser of untrusted input may
crash. (We deliberately do NOT assert "all parsers agree" here — divergences are
expected and are the job of the differential campaign, not a unit test.)
"""
from hypothesis import HealthCheck, given, settings

from cm_difftest.adapters import sut_adapters
from cm_difftest.fuzz.hypothesis_strategies import markdown_documents
from cm_difftest.runner.guard import guarded_render
from cm_difftest.runner.result import Status

_ADAPTERS = sut_adapters()


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(md=markdown_documents)
def test_no_sut_crashes_on_generated_markdown(md):
    for adapter in _ADAPTERS:
        result = guarded_render(adapter, md, timeout_s=5.0)
        assert result.status in (Status.OK, Status.TIMEOUT), (
            f"{adapter.name} raised {result.error!r} on {md!r}"
        )
