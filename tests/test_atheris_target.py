"""Tests for the Atheris crash target's harness logic (spec §8).

We don't run libFuzzer here (that needs the atheris runtime); we test the pure
harness pieces: byte->str decoding must never raise (a decode crash would be a
*harness* bug, not a parser finding — which is exactly what an early fuzz run
caught), and the test callback must tolerate arbitrary inputs.
"""
from cm_difftest.fuzz.atheris_target import _consume, make_test_one_input


def test_consume_never_raises_on_invalid_utf8():
    # incomplete / invalid UTF-8 sequences must decode to a str, not raise
    for data in (b"\xce", b"\x0b(\xce", b"\xff\xfe", b"\x00\x01\x02", bytes(range(256))):
        out = _consume(data)
        assert isinstance(out, str)


def test_consume_roundtrips_ascii_markdown():
    assert _consume(b"*hi* [x](y)") == "*hi* [x](y)"


def test_test_one_input_tolerates_arbitrary_bytes():
    fn = make_test_one_input()
    # benign and adversarial inputs alike must not raise out of the harness
    for data in (b"*hi*", b"\xce\x28", b"#" * 100, b"> " * 50, b"```\n"):
        fn(data)  # should not raise (no SUT crashes on these)
