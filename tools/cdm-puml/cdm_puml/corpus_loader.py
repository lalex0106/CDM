"""Helpers to build a CDM corpus and load manifests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from .compatibility import CdmCorpusDefinition, CdmManifestDefinition, LocalAdapter

DEFAULT_SCHEMA_ROOT = Path("schemaDocuments")
DEFAULT_NAMESPACE = "local"
DEFAULT_ROOT_MANIFEST = "core/core.manifest.cdm.json"


def build_corpus(schema_root: Path | str, ns: str = DEFAULT_NAMESPACE) -> CdmCorpusDefinition:
    """Create a corpus with the provided schema root mounted as *ns*."""

    schema_path = Path(schema_root).resolve()
    corpus = CdmCorpusDefinition()
    corpus.storage.mount(ns, LocalAdapter(str(schema_path)))
    corpus.storage.default_namespace = ns
    return corpus


async def _fetch_manifest_async(
    corpus: CdmCorpusDefinition, cdm_path: str
) -> CdmManifestDefinition:
    if ":/" not in cdm_path:
        cdm_path = f"{corpus.storage.default_namespace}:{cdm_path}"
    obj = await corpus.fetch_object_async(cdm_path)
    if not isinstance(obj, CdmManifestDefinition):  # pragma: no cover - defensive
        raise TypeError(f"Expected a CdmManifestDefinition for {cdm_path!r}, got {type(obj)!r}")
    return obj


def load_manifest(
    corpus: CdmCorpusDefinition,
    cdm_path: str = DEFAULT_ROOT_MANIFEST,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> CdmManifestDefinition:
    """Synchronously load a manifest definition via the corpus."""

    owns_loop = False
    if loop is None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            owns_loop = True
    manifest = loop.run_until_complete(_fetch_manifest_async(corpus, cdm_path))
    if owns_loop:
        loop.close()
    return manifest
