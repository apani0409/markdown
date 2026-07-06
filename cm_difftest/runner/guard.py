"""Guarded execution of a single parse (spec §3 crash class, §7.4).

A parser of untrusted input must never take down the harness: every parse is
wrapped to capture exceptions, enforce a per-input timeout, and (under process
isolation) cap memory and survive hard crashes (segfault/abort/OOM-kill).

Two strategies:

* :func:`guarded_render` — in-process. Fast; uses ``SIGALRM`` for the timeout
  and catches exceptions / ``RecursionError`` / ``MemoryError``. Cannot protect
  against a C-level segfault or a true memory blow-up (use isolation for those).
  The timeout requires the main thread (``SIGALRM`` limitation); off the main
  thread it degrades to "no timeout" rather than failing.
* :func:`guarded_render_isolated` — runs the parse in a forked subprocess with
  ``RLIMIT_AS`` set, so a segfault/abort/OOM becomes a recorded finding instead
  of crashing the runner. Slower; use for the crash class during fuzzing.
"""
from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from time import perf_counter

from cm_difftest.adapters.base import Adapter, Mode
from cm_difftest.runner.result import RenderResult, Status

__all__ = ["guarded_render", "guarded_render_isolated", "TimeoutExceeded"]


class TimeoutExceeded(Exception):
    """Raised internally when a per-input timeout fires."""


@contextmanager
def _time_limit(seconds: float | None):
    if not seconds or seconds <= 0 or threading.current_thread() is not threading.main_thread():
        yield
        return

    def _handler(signum, frame):
        raise TimeoutExceeded()

    old = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def guarded_render(
    adapter: Adapter,
    markdown: str,
    *,
    mode: Mode = Mode.RAW,
    timeout_s: float | None = 5.0,
) -> RenderResult:
    """Render in-process, capturing every failure mode as a :class:`RenderResult`."""
    t0 = perf_counter()
    try:
        with _time_limit(timeout_s):
            html = adapter.render(markdown, mode=mode)
        return RenderResult(adapter.name, Status.OK, html=html, duration_s=perf_counter() - t0)
    except TimeoutExceeded:
        return RenderResult(
            adapter.name, Status.TIMEOUT,
            error=f"timeout > {timeout_s}s", error_type="TimeoutExceeded",
            duration_s=perf_counter() - t0,
        )
    except MemoryError:
        return RenderResult(
            adapter.name, Status.MEMORY,
            error="MemoryError", error_type="MemoryError",
            duration_s=perf_counter() - t0,
        )
    except RecursionError as exc:
        return RenderResult(
            adapter.name, Status.EXCEPTION,
            error=f"RecursionError: {exc}", error_type="RecursionError",
            duration_s=perf_counter() - t0,
        )
    except Exception as exc:  # noqa: BLE001 - intentional: the harness must not die
        return RenderResult(
            adapter.name, Status.EXCEPTION,
            error=f"{type(exc).__name__}: {exc}", error_type=type(exc).__name__,
            duration_s=perf_counter() - t0,
        )


def _isolated_child(queue, adapter_name: str, markdown: str, mode: Mode, memory_mb: int | None):
    # The parent diagnoses hard crashes from the exit code; suppress the child's
    # own fatal-signal traceback so a segfault doesn't spew an (inherited) stack.
    import faulthandler

    faulthandler.disable()
    try:
        if memory_mb:
            import resource

            limit = memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        from cm_difftest.adapters import get_adapter

        html = get_adapter(adapter_name).render(markdown, mode=mode)
        queue.put(("ok", html, None))
    except MemoryError:
        queue.put(("memory", None, "MemoryError"))
    except RecursionError as exc:
        queue.put(("exception", None, f"RecursionError: {exc}"))
    except Exception as exc:  # noqa: BLE001
        queue.put(("exception", None, f"{type(exc).__name__}: {exc}"))


def guarded_render_isolated(
    adapter_name: str,
    markdown: str,
    *,
    mode: Mode = Mode.RAW,
    timeout_s: float = 5.0,
    memory_mb: int | None = 1024,
) -> RenderResult:
    """Render in a forked subprocess so segfault/abort/OOM become findings.

    Identifies the adapter by name (so nothing parser-specific needs pickling).
    """
    import multiprocessing as mp
    import queue as queue_mod

    ctx = mp.get_context("fork")
    q = ctx.Queue()
    proc = ctx.Process(
        target=_isolated_child, args=(q, adapter_name, markdown, mode, memory_mb)
    )
    t0 = perf_counter()
    proc.start()
    proc.join(timeout_s)
    duration = perf_counter() - t0

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return RenderResult(
            adapter_name, Status.TIMEOUT,
            error=f"timeout > {timeout_s}s", error_type="TimeoutExceeded",
            duration_s=duration,
        )

    try:
        kind, html, err = q.get(timeout=0.2)
    except queue_mod.Empty:
        # No result delivered -> the process died hard (segfault/abort/OOM-kill).
        code = proc.exitcode
        # -9 (SIGKILL) is the typical OOM-killer signature.
        status = Status.MEMORY if code == -9 else Status.CRASH
        return RenderResult(
            adapter_name, status,
            error=f"process died (exitcode {code})", error_type="ProcessDeath",
            duration_s=duration,
        )

    if kind == "ok":
        return RenderResult(adapter_name, Status.OK, html=html, duration_s=duration)
    if kind == "memory":
        return RenderResult(
            adapter_name, Status.MEMORY, error=err, error_type="MemoryError",
            duration_s=duration,
        )
    etype = err.split(":", 1)[0] if err else "Exception"
    return RenderResult(
        adapter_name, Status.EXCEPTION, error=err, error_type=etype, duration_s=duration,
    )
