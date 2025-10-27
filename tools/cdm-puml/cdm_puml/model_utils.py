"""Shared helpers for inspecting CDM entity definitions."""

from __future__ import annotations

from typing import Iterable, Iterator

from .compatibility import (
    CdmEntityAttributeDefinition,
    CdmEntityDefinition,
    CdmObjectType,
    CdmTypeAttributeDefinition,
)


def derive_domain(entity_def: CdmEntityDefinition) -> str:
    """Best-effort inference of a domain name for *entity_def*."""

    name = entity_def.entity_name
    if "." in name:
        return name.split(".", 1)[0]
    doc = getattr(entity_def, "in_document", None)
    folder = getattr(doc, "folder", None)
    folder_path = getattr(folder, "folder_path", "")
    parts = [p for p in folder_path.split("/") if p]
    if parts:
        return parts[-1]
    return "Global"


def sanitize_identifier(domain: str, name: str) -> str:
    """Create a PlantUML-safe identifier for *name* within *domain*."""

    identifier = f"{domain}_{name}" if domain else name
    return (
        identifier.replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace(".", "_")
    )


def iter_type_attributes(entity_def: CdmEntityDefinition) -> Iterator[CdmTypeAttributeDefinition]:
    """Yield all direct and nested ``CdmTypeAttributeDefinition`` objects."""

    yield from _walk_type_attributes(getattr(entity_def, "attributes", []) or [])


def iter_entity_attributes(entity_def: CdmEntityDefinition) -> Iterator[CdmEntityAttributeDefinition]:
    """Yield all ``CdmEntityAttributeDefinition`` objects found on *entity_def*."""

    for attr in getattr(entity_def, "attributes", []) or []:
        yield from _walk_entity_attributes(attr)


def _walk_type_attributes(collection: Iterable) -> Iterator[CdmTypeAttributeDefinition]:
    for attr in collection:
        if attr is None:
            continue
        obj_type = getattr(attr, "object_type", None)
        if obj_type == CdmObjectType.TYPE_ATTRIBUTE_DEF:
            yield attr
        elif obj_type == CdmObjectType.ATTRIBUTE_GROUP_REF:
            group = getattr(attr, "explicit_reference", None)
            members = getattr(group, "members", None)
            if members:
                yield from _walk_type_attributes(members)
        elif obj_type == CdmObjectType.ATTRIBUTE_GROUP_DEF:
            members = getattr(attr, "members", None)
            if members:
                yield from _walk_type_attributes(members)
        elif obj_type == CdmObjectType.ENTITY_ATTRIBUTE_DEF:
            continue


def _walk_entity_attributes(attr) -> Iterator[CdmEntityAttributeDefinition]:
    if attr is None:
        return
    obj_type = getattr(attr, "object_type", None)
    if obj_type == CdmObjectType.ENTITY_ATTRIBUTE_DEF:
        yield attr
        return
    if obj_type == CdmObjectType.ATTRIBUTE_GROUP_REF:
        group = getattr(attr, "explicit_reference", None)
        members = getattr(group, "members", None)
        if members:
            for member in members:
                yield from _walk_entity_attributes(member)
    elif obj_type == CdmObjectType.ATTRIBUTE_GROUP_DEF:
        members = getattr(attr, "members", None)
        if members:
            for member in members:
                yield from _walk_entity_attributes(member)

