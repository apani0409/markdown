"""Delta-debugging minimizer for failing inputs (spec §7.7).

Given an interesting input and a predicate that says whether a candidate is
still interesting, shrink to a 1-minimal input using the classic ``ddmin``
algorithm (Zeller & Hildebrand). Results are cached and the number of predicate
evaluations is capped so minimization always terminates.

For differential findings the predicate should preserve the *same* finding (same
category and offenders), not merely "some divergence" — see
:func:`same_divergence_predicate`.
"""
from __future__ import annotations

from collections.abc import Callable

from cm_difftest.runner import DifferentialRunner
from cm_difftest.triage.classifier import classify

__all__ = ["minimize", "same_divergence_predicate", "MinimizeResult"]

Predicate = Callable[[str], bool]


class MinimizeResult(str):
    """A minimized string that also carries the predicate-call count."""

    calls: int

    def __new__(cls, value: str, calls: int):
        obj = super().__new__(cls, value)
        obj.calls = calls
        return obj


def minimize(text: str, predicate: Predicate, *, max_calls: int = 2000) -> MinimizeResult:
    """Return a 1-minimal substring of *text* for which *predicate* still holds.

    If *predicate* does not hold for *text* to begin with, *text* is returned
    unchanged (the caller is responsible for passing an interesting input).
    """
    cache: dict[str, bool] = {}
    calls = 0

    def test(candidate: str) -> bool:
        nonlocal calls
        if candidate in cache:
            return cache[candidate]
        if calls >= max_calls:
            return False  # budget exhausted -> treat as "not interesting"
        calls += 1
        result = predicate(candidate)
        cache[candidate] = result
        return result

    if not predicate(text):
        return MinimizeResult(text, 0)

    s = text
    n = 2
    while len(s) >= 2:
        chunk = max(1, len(s) // n)
        subsets = [s[i : i + chunk] for i in range(0, len(s), chunk)]
        reduced = False

        # Try removing each subset's complement (i.e., keep only one subset) and
        # each complement (remove one subset). ddmin's "remove complement" pass:
        for i in range(len(subsets)):
            complement = "".join(subsets[:i] + subsets[i + 1 :])
            if complement and complement != s and test(complement):
                s = complement
                n = max(n - 1, 2)
                reduced = True
                break

        if reduced:
            continue
        if n >= len(s):
            break
        n = min(len(s), n * 2)

    return MinimizeResult(s, calls)


def same_divergence_predicate(
    runner: DifferentialRunner,
    *,
    expected_html: str | None = None,
    provenance=None,
    category: str | None = None,
    offenders: frozenset[str] | None = None,
) -> Predicate:
    """Build a predicate that holds iff a candidate reproduces the *same* finding.

    "Same" means the same classifier category and the same set of offenders, so
    minimization cannot drift to a different (or weaker) divergence. If
    *category*/*offenders* are omitted, any divergence (non-AGREEMENT) qualifies.
    """
    prov = provenance if provenance is not None else runner.provenance()

    def predicate(candidate: str) -> bool:
        if candidate == "":
            return False
        comp = runner.run(candidate, expected_html=expected_html)
        cls = classify(comp, prov)
        if cls.category.value in ("agreement",):
            return False
        if category is not None and cls.category.value != category:
            return False
        if offenders is not None and frozenset(cls.offenders) != offenders:
            return False
        return True

    return predicate
