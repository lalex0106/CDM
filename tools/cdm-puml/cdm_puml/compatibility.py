"""Compatibility helpers for importing the CDM object model."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "CdmCorpusDefinition",
    "CdmManifestDefinition",
    "CdmEntityDefinition",
    "CdmTypeAttributeDefinition",
    "CdmEntityAttributeDefinition",
    "LocalAdapter",
    "ResolveOptions",
    "CdmObjectType",
]

_MODULE_CANDIDATES = (
    "cdm.objectmodel",
    "commondatamodel.objectmodel",
)


class _ImportError(RuntimeError):
    """Raised when neither CDM namespace is available."""


last_import_error: ImportError | None = None
for module_name in _MODULE_CANDIDATES:
    try:
        objectmodel = import_module(module_name)
        storage = import_module(f"{module_name}.storage")
        utilities = import_module(f"{module_name}.utilities")
        enums = import_module(f"{module_name}.enums")
    except ImportError as exc:  # pragma: no cover - environment dependent
        last_import_error = exc
        continue
    else:
        break
else:  # pragma: no cover - executed when no module found
    raise _ImportError(
        "Unable to import either 'cdm.objectmodel' or 'commondatamodel.objectmodel'."
    ) from last_import_error

CdmCorpusDefinition = objectmodel.CdmCorpusDefinition
CdmManifestDefinition = objectmodel.CdmManifestDefinition
CdmEntityDefinition = objectmodel.CdmEntityDefinition
CdmTypeAttributeDefinition = objectmodel.CdmTypeAttributeDefinition
CdmEntityAttributeDefinition = objectmodel.CdmEntityAttributeDefinition
LocalAdapter = storage.LocalAdapter
ResolveOptions = utilities.ResolveOptions
CdmObjectType = enums.CdmObjectType
