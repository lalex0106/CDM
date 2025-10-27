#!/usr/bin/env python3
"""Generate a simplified PlantUML class diagram from a CDM manifest."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass
class AttributeInfo:
    name: str
    data_type: str
    description: Optional[str] = None


@dataclass
class EntityInfo:
    name: str
    extends: Optional[str]
    attributes: List[AttributeInfo] = field(default_factory=list)


class ManifestReader:
    """Utility for reading manifests and entity documents from disk."""

    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path
        self.base_dir = manifest_path.parent
        self._doc_cache: Dict[Path, Dict] = {}

    def load(self) -> Dict:
        return self._load_json(self.manifest_path)

    def _load_json(self, path: Path) -> Dict:
        if path not in self._doc_cache:
            try:
                self._doc_cache[path] = json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Unable to resolve referenced document: {path}") from exc
        return self._doc_cache[path]

    def resolve_entity(self, entity_path: str) -> Dict:
        """Return the JSON definition of an entity given an entityPath entry."""
        document_name, _, entity_name = entity_path.partition("/")
        document_path = (self.base_dir / document_name).resolve()
        document = self._load_json(document_path)
        for definition in document.get("definitions", []):
            if definition.get("entityName") == entity_name:
                return definition
        raise KeyError(f"Entity '{entity_name}' not found in {document_path}")


def iter_attributes(definition: Dict) -> Iterable[AttributeInfo]:
    for attribute in definition.get("hasAttributes", []):
        if "name" in attribute:
            yield build_attribute(attribute)
        elif "attributeGroupReference" in attribute:
            group = attribute["attributeGroupReference"]
            for member in group.get("members", []):
                if isinstance(member, dict) and "name" in member:
                    yield build_attribute(member)


def build_attribute(attribute: Dict) -> AttributeInfo:
    raw_type = attribute.get("dataType")
    if isinstance(raw_type, dict):
        raw_type = raw_type.get("dataTypeReference") or raw_type.get("entity")
    if raw_type is None:
        raw_type = attribute.get("purpose") or "unknown"
    description = attribute.get("description")
    if not description:
        # Try localized default description.
        for trait in attribute.get("appliedTraits", []):
            if trait.get("traitReference") == "is.localized.describedAs":
                arguments = trait.get("arguments", [])
                if arguments:
                    entity_ref = arguments[0].get("entityReference", {})
                    values = entity_ref.get("constantValues", [])
                    if values and len(values[0]) >= 2:
                        description = values[0][1]
                        break
    return AttributeInfo(name=attribute.get("name", ""), data_type=str(raw_type), description=description)


def collect_entities(reader: ManifestReader, include: Optional[Sequence[str]]) -> List[EntityInfo]:
    manifest = reader.load()
    target_names = {name.strip() for name in include} if include else None
    entities: List[EntityInfo] = []
    for entity in manifest.get("entities", []):
        if entity.get("type") != "LocalEntity":
            continue
        entity_name = entity.get("entityName")
        if target_names and entity_name not in target_names:
            continue
        definition = reader.resolve_entity(entity.get("entityPath", ""))
        entity_info = EntityInfo(name=entity_name, extends=definition.get("extendsEntity"))
        entity_info.attributes.extend(iter_attributes(definition))
        entities.append(entity_info)
    if target_names:
        missing = target_names - {entity.name for entity in entities}
        if missing:
            raise SystemExit(f"Entities not found in manifest: {', '.join(sorted(missing))}")
    return sorted(entities, key=lambda item: item.name)


def render_plantuml(entities: Sequence[EntityInfo]) -> str:
    lines: List[str] = [
        "@startuml",
        "skinparam classAttributeIconSize 0",
        "hide empty methods",
    ]
    for entity in entities:
        lines.append(f"class {entity.name} {{")
        if entity.attributes:
            for attribute in entity.attributes:
                line = f"  +{attribute.name} : {attribute.data_type}"
                if attribute.description:
                    safe_description = attribute.description.replace(chr(10), ' ')
                    line += f" -- {safe_description}"
                lines.append(line)
        lines.append("}")
        if entity.extends:
            lines.append(f"{entity.name} --|> {entity.extends}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to a manifest.cdm.json file")
    parser.add_argument("--entities", nargs="*", help="Optional list of entity names to include")
    parser.add_argument("--output", type=Path, help="Optional path to write the PlantUML text")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    reader = ManifestReader(args.manifest)
    entities = collect_entities(reader, args.entities)
    plantuml_text = render_plantuml(entities)
    if args.output:
        args.output.write_text(plantuml_text, encoding="utf-8")
    else:
        print(plantuml_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
