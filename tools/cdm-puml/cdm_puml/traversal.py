"""Graph traversal utilities for CDM entities."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple

from .compatibility import (
    CdmEntityAttributeDefinition,
    CdmEntityDefinition,
    CdmObjectType,
)
from .inheritance import apply_overrides, discover_inheritance
from .repository import EntityRepository

Relationship = Tuple[str, str, bool, str]


@dataclass
class TraversalResult:
    entities: Set[str]
    relationships: Set[Relationship]
    inheritance_edges: Set[Tuple[str, str]]


CARDINALITY_MANY_MARKERS = {"*", "many", "unbounded", "n"}


def _resolve_target_name(attr: CdmEntityAttributeDefinition) -> str | None:
    if attr.entity is None:
        return None
    if getattr(attr.entity, "named_reference", None):
        return attr.entity.named_reference
    explicit = getattr(attr.entity, "explicit_reference", None)
    if isinstance(explicit, CdmEntityDefinition):
        return explicit.entity_name
    return None


def discover_relationships(
    entity_def: CdmEntityDefinition,
) -> Tuple[List[Relationship], Set[str]]:
    """Extract entity-to-entity relationships defined on *entity_def*."""

    relationships: List[Relationship] = []
    discovered: Set[str] = set()
    attributes = getattr(entity_def, "attributes", []) or []
    for attr in attributes:
        if attr.object_type == CdmObjectType.TYPE_ATTRIBUTE_DEF:  # pragma: no cover - simple branch
            continue
        if attr.object_type != CdmObjectType.ENTITY_ATTRIBUTE_DEF:
            continue
        if not isinstance(attr, CdmEntityAttributeDefinition):
            continue
        target = _resolve_target_name(attr)
        if not target:
            continue
        prop_name = attr.entity.named_reference or attr.name or target
        is_many = False
        card = getattr(attr, "cardinality", None)
        if card is not None:
            maximum = getattr(card, "maximum", None)
            if maximum is None:
                maximum = getattr(card, "max", None)
            if maximum is not None:
                if isinstance(maximum, str) and maximum.lower() in CARDINALITY_MANY_MARKERS:
                    is_many = True
                elif isinstance(maximum, (int, float)) and maximum > 1:
                    is_many = True
        relationships.append((entity_def.entity_name, target, is_many, prop_name))
        discovered.add(target)
    return relationships, discovered


def bfs(
    start_entities: Iterable[str],
    depth: int,
    repo: EntityRepository,
    include_inheritance: bool,
    inheritance_overrides: Dict[str, Dict[str, List[str]]],
    inheritance_scope: str | None,
) -> TraversalResult:
    """Breadth-first traversal of entity relationships."""

    if depth < 1:
        depth = 1
    start_list = list(dict.fromkeys(start_entities))
    repo.ensure_loaded(start_list)

    queue = deque((name, 0) for name in start_list)
    visited: Set[str] = set()
    discovered: Set[str] = set(start_list)
    relationships: Set[Relationship] = set()
    inheritance_edges: Set[Tuple[str, str]] = set()

    while queue:
        current, level = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        entity_def = repo.get(current)
        if entity_def is None:
            continue
        if level < depth:
            rels, referenced = discover_relationships(entity_def)
            for rel in rels:
                relationships.add(rel)
            for ref in referenced:
                if ref not in discovered:
                    discovered.add(ref)
                    queue.append((ref, level + 1))
        if include_inheritance and (
            inheritance_scope == "all" or (inheritance_scope == "start" and level == 0)
        ):
            parents = discover_inheritance(entity_def)
            parents = apply_overrides(parents, inheritance_overrides.get(entity_def.entity_name))
            for parent in parents:
                inheritance_edges.add((parent, entity_def.entity_name))
                if parent not in discovered:
                    discovered.add(parent)
                    queue.append((parent, level + 1))
    return TraversalResult(discovered, relationships, inheritance_edges)
