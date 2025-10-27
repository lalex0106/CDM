"""PlantUML rendering helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

from .compatibility import CdmEntityDefinition, CdmObjectType
from .i18n import I18nDicts, attr_label, entity_label


def _derive_domain(entity_def: CdmEntityDefinition) -> str:
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


def _sanitize_identifier(domain: str, name: str) -> str:
    identifier = f"{domain}_{name}" if domain else name
    return (
        identifier.replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace(".", "_")
    )


def _render_attribute_lines(
    entity_def: CdmEntityDefinition,
    domain: str,
    i18n: I18nDicts,
    lang_primary: str,
    lang_fallback: str,
    bilingual: bool,
) -> list[str]:
    lines: list[str] = []
    for attr in getattr(entity_def, "attributes", []) or []:
        if attr.object_type != CdmObjectType.TYPE_ATTRIBUTE_DEF:
            continue
        name = getattr(attr, "name", "") or "attribute"
        data_ref = getattr(attr, "data_type", None)
        data_type = getattr(data_ref, "named_reference", None)
        if not data_type:
            explicit = getattr(data_ref, "explicit_reference", None)
            data_type = getattr(explicit, "entity_name", None)
        if not data_type:
            data_type = getattr(attr, "data_format", "")
        display = attr_label(i18n, domain, entity_def.entity_name, name, lang_primary, lang_fallback, bilingual)
        lines.append(f"    + {display} : {data_type or 'value'}")
    return lines


def render_entity_block(
    entity_def: CdmEntityDefinition,
    i18n: I18nDicts,
    lang_primary: str,
    lang_fallback: str,
    bilingual: bool,
    show_attributes: bool,
) -> str:
    domain = _derive_domain(entity_def)
    identifier = _sanitize_identifier(domain, entity_def.entity_name)
    label = entity_label(
        i18n, domain, entity_def.entity_name, lang_primary, lang_fallback, bilingual
    )
    stereotype = "Entity"
    header = f"class \"{domain}_{entity_def.entity_name}\\n({label})\" as {identifier} <<{stereotype}>> #0a9396"
    body: list[str] = [header + " {"]
    if show_attributes:
        attr_lines = _render_attribute_lines(
            entity_def, domain, i18n, lang_primary, lang_fallback, bilingual
        )
        body.extend(attr_lines)
        if len(attr_lines) == 0:
            body.append("    ..")
    body.append("}")
    return "\n".join(body)


def render_relationships(
    relationships: Iterable[tuple[str, str, bool, str]],
    i18n: I18nDicts,
    repo,
    lang_primary: str,
    lang_fallback: str,
    bilingual: bool,
) -> list[str]:
    lines: list[str] = []
    for src, dst, is_many, prop in sorted(relationships):
        src_def = repo.get(src)
        dst_def = repo.get(dst)
        src_domain = _derive_domain(src_def) if src_def else ""
        dst_domain = _derive_domain(dst_def) if dst_def else ""
        src_id = _sanitize_identifier(src_domain, src)
        dst_id = _sanitize_identifier(dst_domain, dst)
        label = attr_label(i18n, src_domain, src, prop, lang_primary, lang_fallback, bilingual)
        lines.append(
            f"{src_id} \"1\" -- \"{'0..*' if is_many else '0..1'}\" {dst_id} : {label}"
        )
    return lines


def render_inheritance_edges(edges: Iterable[tuple[str, str]], repo) -> list[str]:
    lines: list[str] = []
    for parent, child in sorted(edges):
        parent_def = repo.get(parent)
        child_def = repo.get(child)
        parent_id = _sanitize_identifier(_derive_domain(parent_def) if parent_def else "", parent)
        child_id = _sanitize_identifier(_derive_domain(child_def) if child_def else "", child)
        lines.append(f"{parent_id} <|-- {child_id}")
    return lines


def compose_puml(
    entity_blocks: Sequence[str],
    relationship_lines: Sequence[str],
    inheritance_lines: Sequence[str],
    theme_file: Optional[Path] = None,
) -> str:
    parts = ["@startuml", "!theme vibrant", "skinparam shadowing true", "left to right direction", "skinparam classAttributeIconSize 0"]
    if theme_file is not None and theme_file.exists():
        parts.append(f"!include {theme_file.as_posix()}")
    parts.append("' --- Entities ---")
    parts.extend(entity_blocks)
    parts.append("' --- Relationships ---")
    parts.extend(relationship_lines)
    if inheritance_lines:
        parts.append("' --- Inheritance ---")
        parts.extend(inheritance_lines)
    parts.append("@enduml")
    return "\n".join(parts)
