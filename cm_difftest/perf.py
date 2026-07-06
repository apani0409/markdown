"""Performance / algorithmic-complexity comparison (DoS class, spec §3).

A parser of untrusted input must not hang or exhaust resources. This module
hunts two robustness problems that the crash/differential passes don't cover:

* **superlinear (e.g. quadratic) scaling** — an input family whose length grows
  linearly but whose parse time grows ~O(n^k), k>1, is an amplification / DoS
  vector;
* **unbounded recursion** — deeply nested block structure that overflows the
  Python stack (``RecursionError``) instead of being bounded.

It measures parse time vs *input size* (not a shape parameter), fits a growth
exponent on a log-log line, and records recursion/timeouts. The cmark C
reference is the robustness baseline.
"""
from __future__ import annotations

import math
import signal
import threading
import time
from dataclasses import dataclass, field

from cm_difftest.adapters import Mode, default_adapters

__all__ = [
    "FAMILIES",
    "Outcome",
    "measure",
    "scaling",
    "growth_exponent",
    "dos_threshold",
    "run_perf",
    "fuzz_amplifiers",
]

# Input families whose *length* is linear in n (so time should be ~linear for a
# well-behaved parser). Each maps n -> markdown string.
FAMILIES: dict[str, callable] = {
    "balanced_brackets": lambda n: "[" * n + "]" * n,
    "open_brackets": lambda n: "[" * n,
    "link_open_runs": lambda n: "[](" * n,
    "link_label_runs": lambda n: "[a]" * n,
    "image_open_runs": lambda n: "![" * n,
    "emphasis_run": lambda n: "*" * n + "a",
    "emphasis_alt": lambda n: "*_" * n,
    "backtick_run": lambda n: "`" * n + "a",
    "blockquote_depth": lambda n: ">" * n + " x",
    "angle_run": lambda n: "<" * n,
    "paren_nest_in_link": lambda n: "[a](" + "(" * n + ")" * n + ")",
}

# Families that exercise block-nesting depth (recursion risk).
_RECURSION_FAMILIES = {"blockquote_depth"}


class _Timeout(Exception):
    pass


def measure(adapter, md: str, *, budget: float = 10.0) -> tuple[str, float]:
    """Render once under a time budget. Returns (status, seconds).

    status ∈ {"ok", "timeout", "recursion", "error"}; seconds is the elapsed
    time for "ok"/"recursion" (best effort) or the budget for "timeout".
    """
    use_alarm = threading.current_thread() is threading.main_thread() and budget
    if use_alarm:
        def _h(signum, frame):
            raise _Timeout()

        old = signal.signal(signal.SIGALRM, _h)
        signal.setitimer(signal.ITIMER_REAL, budget)
    t0 = time.perf_counter()
    try:
        adapter.render(md, mode=Mode.RAW)
        return "ok", time.perf_counter() - t0
    except _Timeout:
        return "timeout", budget
    except RecursionError:
        return "recursion", time.perf_counter() - t0
    except Exception:  # noqa: BLE001
        return "error", time.perf_counter() - t0
    finally:
        if use_alarm:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)


def _median_time(adapter, md: str, *, budget: float, repeats: int = 3) -> tuple[str, float]:
    times = []
    for _ in range(repeats):
        status, secs = measure(adapter, md, budget=budget)
        if status != "ok":
            return status, secs
        times.append(secs)
    times.sort()
    return "ok", times[len(times) // 2]


@dataclass
class Outcome:
    family: str
    adapter: str
    sizes: list[int]  # input lengths in chars
    times: list[float]  # seconds (or sentinel)
    statuses: list[str]
    exponent: float | None = None  # fitted log-log growth exponent
    status: str = "ok"  # worst status seen: ok|recursion|timeout|error
    note: str = ""


def growth_exponent(sizes: list[int], times: list[float]) -> float | None:
    """Least-squares slope of log(time) vs log(size) over the OK points."""
    pts = [(s, t) for s, t in zip(sizes, times) if t and t > 1e-6]
    if len(pts) < 2:
        return None
    xs = [math.log(s) for s, _ in pts]
    ys = [math.log(t) for _, t in pts]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom


def scaling(adapter, family: str, ns: list[int], *, budget: float = 10.0) -> Outcome:
    mk = FAMILIES[family]
    sizes, times, statuses = [], [], []
    worst = "ok"
    for n in ns:
        md = mk(n)
        status, secs = _median_time(adapter, md, budget=budget)
        sizes.append(len(md))
        times.append(secs if status in ("ok", "recursion") else float("inf"))
        statuses.append(status)
        if status != "ok":
            worst = status
            break  # no point growing further once it breaks
    ok_sizes = [s for s, st in zip(sizes, statuses) if st == "ok"]
    ok_times = [t for t, st in zip(times, statuses) if st == "ok"]
    exp = growth_exponent(ok_sizes, ok_times)
    return Outcome(family, adapter.name, sizes, times, statuses, exponent=exp, status=worst)


def dos_threshold(adapter, family: str, *, target_seconds: float = 1.0,
                  max_n: int = 200000, budget: float = 12.0) -> int | None:
    """Smallest n whose parse exceeds *target_seconds* (amplification factor).

    Returns the input length in chars, or None if not reached by max_n.
    """
    mk = FAMILIES[family]
    n = 256
    while n <= max_n:
        md = mk(n)
        status, secs = measure(adapter, md, budget=budget)
        if status in ("timeout", "recursion", "error") or secs >= target_seconds:
            return len(md)
        n *= 2
    return None


def fuzz_amplifiers(
    adapters=None,
    *,
    seed: int = 0,
    n_fragments: int = 600,
    reps=(1000, 2000, 4000, 8000),
    budget: float = 5.0,
    exponent_threshold: float = 1.6,
    reference: str = "cmark",
) -> list[dict]:
    """Auto-discover amplifier fragments: short snippets whose *repetition*
    makes a parser superlinear (or recurse) while the reference stays ~linear.

    Returns a list of {parser, fragment, kind, exponent, ref_exponent}. Used to
    find DoS patterns beyond the hand-picked FAMILIES (deterministic per seed).
    """
    import random

    adapters = adapters if adapters is not None else default_adapters()
    by_name = {a.name: a for a in adapters}
    ref = by_name.get(reference)
    toks = list("*_`~[]()!>#-+\\<>& a\"'|:.")
    rng = random.Random(seed)
    frags = {"".join(rng.choice(toks) for _ in range(rng.randint(2, 6))) for _ in range(n_fragments)}

    results = []
    for frag in frags:
        if not frag.strip():
            continue
        for a in adapters:
            if a.name == reference:
                continue
            sizes, times, rec = [], [], False
            for r in reps:
                md = frag * r
                status, secs = measure(a, md, budget=budget)
                if status == "recursion":
                    rec = True
                    break
                sizes.append(len(md))
                times.append(secs if status == "ok" else float("inf"))
            if rec:
                results.append({"parser": a.name, "fragment": frag, "kind": "recursion",
                                "exponent": None, "ref_exponent": None})
                continue
            ok = [(s, t) for s, t in zip(sizes, times) if t != float("inf")]
            exp = growth_exponent([s for s, _ in ok], [t for _, t in ok])
            if exp is not None and exp > exponent_threshold and ref is not None:
                rsizes, rtimes = [], []
                for r in reps:
                    st, sc = measure(ref, frag * r, budget=budget)
                    if st == "ok":
                        rsizes.append(len(frag * r)); rtimes.append(sc)
                rexp = growth_exponent(rsizes, rtimes)
                if rexp is None or rexp < 1.3:
                    results.append({"parser": a.name, "fragment": frag, "kind": "superlinear",
                                    "exponent": round(exp, 2),
                                    "ref_exponent": None if rexp is None else round(rexp, 2)})
    return results


def run_perf(adapters=None, ns=(500, 1000, 2000, 4000, 8000), *, budget: float = 10.0) -> list[Outcome]:
    adapters = adapters if adapters is not None else default_adapters()
    out = []
    for family in FAMILIES:
        family_ns = (200, 400, 800, 1600) if family in _RECURSION_FAMILIES else list(ns)
        for a in adapters:
            out.append(scaling(a, family, list(family_ns), budget=budget))
    return out
