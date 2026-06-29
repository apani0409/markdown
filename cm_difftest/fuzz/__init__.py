"""Fuzz subpackage: structure-aware generator, Hypothesis strategies, Atheris
targets, and the differential fuzzing campaign (spec §8)."""

from cm_difftest.fuzz.generator import StructureAwareGenerator
from cm_difftest.fuzz.mutators import MUTATORS, mutate_once

__all__ = ["StructureAwareGenerator", "MUTATORS", "mutate_once"]
