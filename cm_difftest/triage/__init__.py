"""Triage subpackage: classifier (M1) + minimizer/triage log (M2) (spec §7.5)."""

from cm_difftest.triage.classifier import Category, Classification, classify

__all__ = ["Category", "Classification", "classify"]
