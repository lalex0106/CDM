"""Command line interface for CDM → PlantUML generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import yaml

from .compatibility import ResolveOptions
from .corpus_loader import DEFAULT_ROOT_MANIFEST, build_corpus, load_manifest
from .inheritance import load_overrides
from .i18n import I18nDicts, load_translations
from .logging_conf import configure_logging, get_logger
from .render import (
    compose_puml,
    render_entity_block,
    render_inheritance_edges,
    render_relationships,
)
from .repository import EntityRepository
from .traversal import TraversalResult, bfs

DEFAULT_RESOURCES = ["Product", "Service", "Customer"]
DEFAULT_I18N_ROOT = Path(__file__).resolve().parent.parent / "overrides" / "i18n"
DEFAULT_THEME = Path(__file__).resolve().parent.parent / "config" / "theme.puml"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "dist" / "puml" / "model.puml"
DEFAULT_INDEX = Path(__file__).resolve().parent.parent / "dist" / "docs" / "api_resources.yaml"

LOGGER = get_logger(__name__)


def _resolve_langs(args: argparse.Namespace) -> tuple[str, str, bool]:
    primary = args.label_language or "zh"
    fallback = args.fallback_language or "en"
    bilingual = bool(args.bilingual) or args.language_mode == "both"
    if args.language_mode == "en":
        primary = "en"
        fallback = args.fallback_language or "zh"
        bilingual = False
    elif args.language_mode == "zh":
        primary = "zh"
        fallback = args.fallback_language or "en"
    return primary, fallback, bilingual


def _load_repo(manifest_path: str, schema_root: Path) -> EntityRepository:
    corpus = build_corpus(schema_root)
    manifest = load_manifest(corpus, manifest_path)
    res_opt = ResolveOptions(wrt_doc=manifest)
    repo = EntityRepository(corpus=corpus, res_opt=res_opt)
    repo.load_all(manifest)
    return repo


def _write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    LOGGER.info("Wrote %s", path)


def _generate_diagram(
    repo: EntityRepository,
    translations: I18nDicts,
    args: argparse.Namespace,
    resources: Sequence[str],
    overrides_map,
    output_path: Path,
) -> tuple[str, TraversalResult]:
    primary_lang, fallback_lang, bilingual = _resolve_langs(args)
    include_inheritance = not args.no_inheritance
    scope = args.inheritance_scope
    result = bfs(
        start_entities=resources,
        depth=args.depth,
        repo=repo,
        include_inheritance=include_inheritance,
        inheritance_overrides=overrides_map,
        inheritance_scope=scope,
    )
    entity_blocks = []
    for name in sorted(result.entities):
        entity_def = repo.get(name)
        if not entity_def:
            LOGGER.debug("Entity %s missing from repository", name)
            continue
        entity_blocks.append(
            render_entity_block(
                entity_def,
                translations,
                primary_lang,
                fallback_lang,
                bilingual,
                not args.hide_attributes,
            )
        )
    relationship_lines = render_relationships(
        result.relationships,
        translations,
        repo,
        primary_lang,
        fallback_lang,
        bilingual,
    )
    inheritance_lines = render_inheritance_edges(result.inheritance_edges, repo)
    theme_path = args.theme or DEFAULT_THEME
    puml = compose_puml(entity_blocks, relationship_lines, inheritance_lines, theme_path)
    _write_output(output_path, puml)
    return puml, result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CDM to PlantUML visualiser")
    parser.add_argument(
        "--resources",
        "-r",
        nargs="+",
        default=DEFAULT_RESOURCES,
        help="Starting entities for traversal",
    )
    parser.add_argument("--depth", "-d", type=int, default=2, help="Traversal depth")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="PlantUML output file",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("schemaDocuments"),
        help="Root of the schema repository",
    )
    parser.add_argument("--source-root", type=Path, default=None, help="API docs root (reserved)")
    parser.add_argument(
        "--i18n-root",
        type=Path,
        default=DEFAULT_I18N_ROOT,
        help="Path to translation overrides",
    )
    parser.add_argument("--versions", nargs="*", help="Version filter (reserved)")
    parser.add_argument("--api", default=None, help="API selection (reserved)")
    parser.add_argument("--label-language", default="zh", help="Primary label language")
    parser.add_argument("--fallback-language", default="en", help="Fallback label language")
    parser.add_argument("--bilingual", action="store_true", help="Always show bilingual labels")
    parser.add_argument(
        "--language-mode",
        choices=["zh", "en", "both"],
        default="both",
        help="Convenience language mode",
    )
    parser.add_argument("--list", action="store_true", help="List entities only")
    parser.add_argument("--list-apis", action="store_true", help="List available APIs (reserved)")
    parser.add_argument(
        "--dump-resource-index",
        type=Path,
        default=DEFAULT_INDEX,
        help="Write discovered resources index",
    )
    parser.add_argument(
        "--emit-version-diagrams",
        action="store_true",
        help="Batch generate per-version diagrams (reserved)",
    )
    parser.add_argument(
        "--inheritance-config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "config" / "inheritance_overrides.yaml",
        help="Overrides for inheritance graph",
    )
    parser.add_argument("--no-inheritance", action="store_true", help="Disable inheritance edges")
    parser.add_argument(
        "--inheritance-scope",
        choices=["start", "all"],
        default="all",
        help="Control which entities expand inheritance",
    )
    parser.add_argument("--batch-roots", action="store_true", help="Enable batch root processing")
    parser.add_argument(
        "--batch-roots-config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "config" / "roots.yaml",
        help="Batch roots configuration file",
    )
    parser.add_argument(
        "--batch-roots-output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "dist",
        help="Batch roots output directory",
    )
    parser.add_argument(
        "--hide-attributes",
        action="store_true",
        help="Hide attributes on entity blocks",
    )
    parser.add_argument(
        "--theme",
        type=Path,
        default=None,
        help="Optional PlantUML theme snippet",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument(
        "--manifest",
        default=DEFAULT_ROOT_MANIFEST,
        help="Manifest path relative to repo root",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    if args.list_apis:
        LOGGER.info("API listing is not yet implemented")
        return 0

    schema_root = args.repo.resolve()
    if not schema_root.exists():
        parser.error(f"Schema repository path not found: {schema_root}")

    overrides_map = load_overrides(args.inheritance_config)
    translations = load_translations(args.i18n_root)

    repo = _load_repo(args.manifest, schema_root)

    if args.list:
        for name in repo.all_names():
            print(name)
        return 0

    if args.batch_roots:
        config_path = args.batch_roots_config
        if not config_path.exists():
            parser.error(f"Batch roots config not found: {config_path}")
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        groups = config.get("roots", []) if isinstance(config, dict) else config
        for group in groups:
            name = group.get("name") or "batch"
            resources = group.get("resources") or DEFAULT_RESOURCES
            output_dir = args.batch_roots_output / "puml"
            output_path = output_dir / f"{name}.puml"
            _, batch_result = _generate_diagram(
                repo,
                translations,
                args,
                resources,
                overrides_map,
                output_path,
            )
            LOGGER.info(
                "Batch group %s: %d entities, %d relationships",
                name,
                len(batch_result.entities),
                len(batch_result.relationships),
            )
        return 0

    puml, traversal = _generate_diagram(
        repo,
        translations,
        args,
        args.resources,
        overrides_map,
        args.output,
    )

    if args.dump_resource_index:
        index_path = Path(args.dump_resource_index)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"resources": sorted(traversal.entities)}
        index_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        LOGGER.info("Resource index written to %s", index_path)

    if args.emit_version_diagrams:
        LOGGER.info("Version diagrams emission is reserved for future use")

    if not puml:
        LOGGER.warning("No PlantUML generated")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
