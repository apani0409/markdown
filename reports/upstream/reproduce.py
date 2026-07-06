#!/usr/bin/env python3
"""Standalone minimal reproducers for the differential findings (no cm-difftest).

Run with the pinned versions (markdown-it-py 4.2.0, mistletoe 1.5.1, marko 2.2.3)
and the cmark 0.31.2 reference. Each case prints every implementation's output so
maintainers can confirm independently. The "expected" value is the spec-correct
output, which the cmark 0.31.2 reference and at least one pure-Python parser also
produce.

    python reports/upstream/reproduce.py
"""
from markdown_it import MarkdownIt
import mistletoe
import marko

mdit = MarkdownIt("commonmark")


def render_all(md: str) -> dict:
    return {
        "markdown-it-py": mdit.render(md),
        "mistletoe": mistletoe.markdown(md),
        "marko": marko.Markdown()(md),
    }


CASES = [
    # (input, expected spec-correct HTML, offender(s), one-line description)
    ("*", "<ul>\n<li></li>\n</ul>\n", "marko",
     "lone bullet marker at EOF -> empty list item (List items, e.g. spec ex. 278)"),
    ("-", "<ul>\n<li></li>\n</ul>\n", "marko",
     "lone '-' marker at EOF -> empty list item"),
    ("1.", "<ol>\n<li></li>\n</ol>\n", "marko",
     "lone ordered marker at EOF -> empty list item"),
    ("<!", "<p>&lt;!</p>\n", "marko",
     "'<!' is NOT an HTML block (type 4 needs '<!' + ASCII letter; spec lines ~2388) -> escaped text"),
    ("[](;)", '<p><a href=";"></a></p>\n', "marko",
     "URL sub-delimiter ';' must not be percent-encoded to %3B"),
    ("[`t`>`", "<p>[<code>t</code>&gt;`</p>\n", "markdown-it-py",
     "code span must be recognized (Code spans, spec ex. 328-349)"),
    ("- --", "<p>- --</p>\n", "marko + mistletoe",
     "'-<NBSP>--' is NOT a thematic break (only spaces/tabs allowed; spec lines ~874) -> paragraph"),
]


CRASH_CASE = '****"************+****'


def show_crash() -> None:
    print("=" * 72)
    print("CRASH CLASS (highest severity): mistletoe raises on this input,")
    print("while markdown-it-py, marko, and cmark all render it.")
    print(f"input: {CRASH_CASE!r}")
    print("  root cause: mistletoe/core_tokens.py process_emphasis -> closer.type[0]")
    for name, fn in (
        ("markdown-it-py", lambda s: mdit.render(s)),
        ("mistletoe", mistletoe.markdown),
        ("marko", lambda s: marko.Markdown()(s)),
    ):
        try:
            fn(CRASH_CASE)
            print(f"  {name:15} OK (no crash)")
        except Exception as exc:  # noqa: BLE001
            print(f"  {name:15} CRASH: {type(exc).__name__}: {exc}")


def show_perf() -> None:
    import time

    print("=" * 72)
    print("DoS CLASS: mistletoe is O(n^2) on linear runs of brackets, while")
    print("markdown-it-py and marko stay ~linear (cmark too). A few KB pins the")
    print("CPU for seconds. (Fixed by patches/mistletoe/0003..0005-*.patch:")
    print("rescan-per-']', O(n) opener removal, and an uncapped link-dest scan.)")
    impls = (
        ("markdown-it-py", lambda s: mdit.render(s)),
        ("mistletoe", mistletoe.markdown),
        ("marko", lambda s: marko.Markdown()(s)),
    )
    families = {
        "']'*n": lambda n: "]" * n,
        "'[]('*n": lambda n: "[](" * n,
    }
    sizes = (1000, 2000, 4000, 8000)
    for fam, mk in families.items():
        print(f"-- input family {fam} --")
        for name, fn in impls:
            times = []
            for n in sizes:
                t0 = time.perf_counter()
                fn(mk(n))
                times.append(time.perf_counter() - t0)
            ratio = times[-1] / times[0] if times[0] else float("inf")
            shape = "QUADRATIC" if ratio > 20 else "~linear"
            cols = "  ".join(f"n={n}:{t:.4f}s" for n, t in zip(sizes, times))
            print(f"  {name:15} {cols}   8x->{ratio:.0f}x  [{shape}]")


def main() -> None:
    show_crash()
    show_perf()
    for md, expected, offender, desc in CASES:
        print("=" * 72)
        print(f"input:    {md!r}")
        print(f"desc:     {desc}")
        print(f"offender: {offender}")
        print(f"expected: {expected!r}   (cmark 0.31.2 agrees)")
        for name, out in render_all(md).items():
            flag = "  <-- differs" if out != expected else ""
            print(f"  {name:15} {out!r}{flag}")
    print("=" * 72)


if __name__ == "__main__":
    main()
