"""Generate blank translation templates for CDM entities and attributes."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from cdm_puml.compatibility import ResolveOptions
from cdm_puml.corpus_loader import DEFAULT_ROOT_MANIFEST, build_corpus, load_manifest
from cdm_puml.model_utils import derive_domain, iter_entity_attributes, iter_type_attributes
from cdm_puml.repository import EntityRepository

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "dist" / "i18n" / "templates"


def _normalise_languages(languages: Iterable[str]) -> List[str]:
    seen: dict[str, None] = {}
    for lang in languages:
        if not lang:
            continue
        norm = lang.lower()
        seen.setdefault(norm, None)
    return list(seen.keys()) or ["zh"]


def _attribute_name(attr) -> str | None:
    name = getattr(attr, "name", None)
    if name:
        return str(name)
    named_reference = getattr(attr, "named_reference", None)
    if named_reference:
        return str(named_reference)
    entity_ref = getattr(attr, "entity", None)
    named_reference = getattr(entity_ref, "named_reference", None)
    if named_reference:
        return str(named_reference)
    explicit = getattr(entity_ref, "explicit_reference", None) if entity_ref else None
    entity_name = getattr(explicit, "entity_name", None)
    if entity_name:
        return str(entity_name)
    return None


def _collect_rows(repo: EntityRepository, languages: Sequence[str]) -> Tuple[List[dict], List[dict]]:
    entity_rows: List[dict] = []
    attribute_rows: List[dict] = []
    attribute_keys: set[tuple[str, str, str]] = set()

    for entity_name in repo.all_names():
        entity_def = repo.get(entity_name)
        if entity_def is None:
            continue
        domain = derive_domain(entity_def)
        for lang in languages:
            entity_rows.append(
                {
                    "domain": domain,
                    "name": entity_name,
                    "lang": lang,
                    "label": "",
                }
            )
        for attr in iter_type_attributes(entity_def):
            attr_name = _attribute_name(attr)
            if not attr_name:
                continue
            key = (domain, entity_name, attr_name)
            if key in attribute_keys:
                continue
            attribute_keys.add(key)
            for lang in languages:
                attribute_rows.append(
                    {
                        "domain": domain,
                        "entity": entity_name,
                        "attr": attr_name,
                        "lang": lang,
                        "label": "",
                    }
                )
        for attr in iter_entity_attributes(entity_def):
            attr_name = _attribute_name(attr)
            if not attr_name:
                continue
            key = (domain, entity_name, attr_name)
            if key in attribute_keys:
                continue
            attribute_keys.add(key)
            for lang in languages:
                attribute_rows.append(
                    {
                        "domain": domain,
                        "entity": entity_name,
                        "attr": attr_name,
                        "lang": lang,
                        "label": "",
                    }
                )

    entity_rows.sort(key=lambda row: (row["domain"], row["name"], row["lang"]))
    attribute_rows.sort(
        key=lambda row: (row["domain"], row["entity"], row["attr"], row["lang"])
    )
    return entity_rows, attribute_rows


def _write_csv(path: Path, rows: Sequence[dict], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def _write_xlsx(path: Path, rows: Sequence[dict], columns: Sequence[str]) -> None:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("pandas is required for Excel output") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=columns)
    df.to_excel(path, index=False)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dump CDM translation templates")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("schemaDocuments"),
        help="Root of the schema repository (defaults to schemaDocuments)",
    )
    parser.add_argument(
        "--manifest",
        default=DEFAULT_ROOT_MANIFEST,
        help="Manifest path relative to the mounted namespace",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write template files into",
    )
    parser.add_argument(
        "--languages",
        "-l",
        nargs="+",
        default=["zh"],
        help="Language codes to pre-populate in the template",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "xlsx", "both"],
        default="csv",
        help="Output file format",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    languages = _normalise_languages(args.languages)

    corpus = build_corpus(args.repo)
    manifest = load_manifest(corpus, args.manifest)
    res_opt = ResolveOptions(wrt_doc=manifest)
    repo = EntityRepository(corpus=corpus, res_opt=res_opt)
    repo.load_all(manifest)

    entity_rows, attribute_rows = _collect_rows(repo, languages)

    columns_entities = ["domain", "name", "lang", "label"]
    columns_attributes = ["domain", "entity", "attr", "lang", "label"]

    if args.format in {"csv", "both"}:
        entities_path = args.output_dir / "entities_template.csv"
        attributes_path = args.output_dir / "attributes_template.csv"
        _write_csv(entities_path, entity_rows, columns_entities)
        _write_csv(attributes_path, attribute_rows, columns_attributes)
        print(f"Wrote {entities_path} ({len(entity_rows)} rows)")
        print(f"Wrote {attributes_path} ({len(attribute_rows)} rows)")

    if args.format in {"xlsx", "both"}:
        entities_xlsx = args.output_dir / "entities_template.xlsx"
        attributes_xlsx = args.output_dir / "attributes_template.xlsx"
        _write_xlsx(entities_xlsx, entity_rows, columns_entities)
        _write_xlsx(attributes_xlsx, attribute_rows, columns_attributes)
        print(f"Wrote {entities_xlsx} ({len(entity_rows)} rows)")
        print(f"Wrote {attributes_xlsx} ({len(attribute_rows)} rows)")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
