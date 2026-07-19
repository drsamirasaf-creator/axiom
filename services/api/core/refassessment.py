"""Canonical AXIOM Assessment taxonomy — versioned platform content (7d-1).

Mirrors refcompanies.py: the framework's seed content lives here as pinned,
versioned reference data so taxonomy updates are DELIBERATE. To roll a new
taxonomy: add a new versioned JSON to assets/, then bump TAXONOMY_VERSION and
TAXONOMY_FILE here. Existing per-company frameworks keep the revision they were
seeded with; only fresh first-touches use the current version.

axiom_assessment_taxonomy_v1.json: 13 L1 (definitions + default weights),
78 L2 (definitions), 361 L3 children (code + title).
"""
import json
import os

TAXONOMY_VERSION = "v1"
TAXONOMY_FILE = "axiom_assessment_taxonomy_v1.json"


def taxonomy() -> dict:
    """The canonical taxonomy dict: {version, source_note, categories:[...]}."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets",
                        TAXONOMY_FILE)
    with open(path) as f:
        return json.load(f)
