"""Tests for the structure-aware mutators and seeded generator (spec §8)."""
import random

import pytest

from cm_difftest.fuzz.mutators import MUTATORS, mutate_once
from cm_difftest.fuzz.generator import StructureAwareGenerator

SAMPLES = ["", "*hi*", "a\nb\n", "[x](y)", "<div>z</div>", "# h\n\ntext", "1. a\n2. b"]


@pytest.mark.parametrize("name,fn,weight", MUTATORS)
def test_each_mutator_returns_str_and_never_raises(name, fn, weight):
    rng = random.Random(123)
    for s in SAMPLES:
        out = fn(s, rng)
        assert isinstance(out, str)
    assert weight >= 1


def test_mutate_once_reports_operator_name():
    rng = random.Random(1)
    name, out = mutate_once("*x*", rng)
    assert name in {m[0] for m in MUTATORS}
    assert isinstance(out, str)


def test_generator_is_deterministic_for_same_seed():
    g1 = StructureAwareGenerator(SAMPLES, seed=42)
    g2 = StructureAwareGenerator(SAMPLES, seed=42)
    assert g1.take(50) == g2.take(50)


def test_generator_differs_across_seeds():
    a = StructureAwareGenerator(SAMPLES, seed=1).take(50)
    b = StructureAwareGenerator(SAMPLES, seed=2).take(50)
    assert a != b


def test_generator_take_count_and_types():
    out = StructureAwareGenerator(SAMPLES, seed=7).take(30)
    assert len(out) == 30
    assert all(isinstance(s, str) for s in out)


def test_generator_robustness_many_inputs():
    # The generator must never raise across a long run.
    gen = StructureAwareGenerator(SAMPLES, seed=99, max_mutations=6)
    for s in gen.take(1000):
        assert isinstance(s, str)


def test_generator_handles_empty_seed_list():
    gen = StructureAwareGenerator([], seed=0)
    assert all(isinstance(s, str) for s in gen.take(10))
