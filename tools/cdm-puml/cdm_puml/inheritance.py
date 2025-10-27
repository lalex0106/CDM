"""Utilities for understanding entity inheritance relationships."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Dict, Set

import yaml

from .compatibility import CdmEntityDefinition


def discover_inheritance(entity_def: CdmEntityDefinition) -> Set[str]:
    """Return the set of base entity names for *entity_def*."""

    parents: Set[str] = set()
    extends = getattr(entity_def, "extends_entity", None)
    if extends and getattr(extends, "named_reference", None):
        parents.add(extends.named_reference)
    return parents


def load_overrides(path) -> Dict[str, Dict[str, list[str]]]:
    if path is None:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    normalised: Dict[str, Dict[str, list[str]]] = {}
    for entity, options in data.items():
        if not isinstance(options, dict):
            continue
        normalised[entity] = {}
        for key in ("add", "remove", "replace"):
            value = options.get(key)
            if isinstance(value, str):
                normalised[entity][key] = [value]
            elif isinstance(value, Iterable):
                normalised[entity][key] = [str(v) for v in value]
    return normalised


def apply_overrides(parents: Set[str], overrides: Dict[str, list[str]] | None) -> Set[str]:
    if not overrides:
        return set(parents)
    result = set(parents)
    if "replace" in overrides:
        result = set(overrides["replace"])
    if "remove" in overrides:
        result.difference_update(overrides["remove"])
    if "add" in overrides:
        result.update(overrides["add"])
    return result
