"""Entity repository for convenient lookup and caching."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .compatibility import (
    CdmEntityDefinition,
    CdmManifestDefinition,
    ResolveOptions,
)


@dataclass
class EntityRepository:
    """Materialised view over a manifest's local entities."""

    corpus
    res_opt: ResolveOptions
    _entities: Dict[str, CdmEntityDefinition] = field(default_factory=dict)

    def load_all(self, manifest: CdmManifestDefinition) -> None:
        """Load all local entity definitions from *manifest*."""

        for entity_decl in manifest.entities:
            try:
                entity_def = entity_decl.fetch_object_definition(self.res_opt)
            except Exception as exc:  # pragma: no cover - cdm errors are environment specific
                raise RuntimeError(
                    f"Failed to resolve entity definition for {entity_decl.entity_name!r}: {exc}"
                ) from exc
            if isinstance(entity_def, CdmEntityDefinition):
                self._entities[entity_decl.entity_name] = entity_def

    def get(self, name: str) -> Optional[CdmEntityDefinition]:
        return self._entities.get(name)

    def all_names(self) -> List[str]:
        return sorted(self._entities)

    def ensure_loaded(self, names: Iterable[str]) -> None:
        missing = [n for n in names if n not in self._entities]
        if missing:
            raise KeyError(f"Entities not found in repository: {', '.join(missing)}")
