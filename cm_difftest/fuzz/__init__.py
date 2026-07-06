"""Fuzz subpackage: structure-aware generator, Hypothesis strategies, Atheris
targets, and the differential fuzzing campaign (spec §8)."""

from cm_difftest.fuzz.campaign import CampaignConfig, CampaignResult, run_campaign
from cm_difftest.fuzz.generator import StructureAwareGenerator, corpus_seeds
from cm_difftest.fuzz.mutators import MUTATORS, mutate_once

__all__ = [
    "StructureAwareGenerator",
    "corpus_seeds",
    "MUTATORS",
    "mutate_once",
    "CampaignConfig",
    "CampaignResult",
    "run_campaign",
]
