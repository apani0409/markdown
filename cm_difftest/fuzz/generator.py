"""Structure-aware, seeded input generator (spec §8).

Starts from seeds (the spec.txt examples are the proven starting region) and
applies 1..k structure-aware mutations, optionally splicing two seeds. Fully
deterministic: a given ``seed`` reproduces the exact input sequence, so every
finding is reproducible (spec §8 determinism requirement).
"""
from __future__ import annotations

import random
from collections.abc import Iterable, Iterator

from cm_difftest.fuzz.mutators import mutate_once

__all__ = ["StructureAwareGenerator", "corpus_seeds"]


def corpus_seeds() -> list[str]:
    """The spec.txt example inputs, the canonical fuzzing seeds."""
    from cm_difftest.corpus import load_spec

    return [e.markdown for e in load_spec()]


class StructureAwareGenerator:
    def __init__(
        self,
        seeds: Iterable[str],
        *,
        seed: int = 0,
        max_mutations: int = 4,
        splice_prob: float = 0.15,
    ) -> None:
        self.seeds = [s for s in seeds]
        if not self.seeds:
            self.seeds = [""]
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_mutations = max_mutations
        self.splice_prob = splice_prob

    def _splice(self, a: str, b: str) -> str:
        i = self.rng.randint(0, len(a))
        j = self.rng.randint(0, len(b))
        return a[:i] + b[j:]

    def generate_one(self) -> str:
        base = self.rng.choice(self.seeds)
        if self.rng.random() < self.splice_prob:
            base = self._splice(base, self.rng.choice(self.seeds))
        n = self.rng.randint(1, self.max_mutations)
        text = base
        for _ in range(n):
            _, text = mutate_once(text, self.rng)
        return text

    def take(self, n: int) -> list[str]:
        return [self.generate_one() for _ in range(n)]

    def __iter__(self) -> Iterator[str]:
        while True:
            yield self.generate_one()
