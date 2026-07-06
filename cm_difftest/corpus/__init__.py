"""Corpus subpackage: spec.txt loader and the pinned spec asset (spec §7.2)."""

from cm_difftest.corpus.loader import Example, default_spec_path, load_spec, SPEC_VERSION

__all__ = ["Example", "load_spec", "default_spec_path", "SPEC_VERSION"]
