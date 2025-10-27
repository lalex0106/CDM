"""Translation helpers for entity and attribute labels."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


@dataclass
class I18nDicts:
    entities: Dict[tuple[str, str, str], str]
    attributes: Dict[tuple[str, str, str, str], str]


def _load_table(path: Path, expected_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=expected_columns)
    if path.suffix.lower() in {".xls", ".xlsx"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns {missing!r} in translation file {path}")
    return df[expected_columns].fillna("")


def load_translations(i18n_root: Path) -> I18nDicts:
    entities_path = i18n_root / "entities.csv"
    attributes_path = i18n_root / "attributes.csv"
    entities_df = _load_table(entities_path, ["domain", "name", "lang", "label"])
    attrs_df = _load_table(
        attributes_path, ["domain", "entity", "attr", "lang", "label"]
    )
    entity_map = {
        (row.domain or "", row.name, row.lang): row.label
        for row in entities_df.itertuples(index=False)
        if row.label
    }
    attr_map = {
        (row.domain or "", row.entity, row.attr, row.lang): row.label
        for row in attrs_df.itertuples(index=False)
        if row.label
    }
    return I18nDicts(entity_map, attr_map)


def _compose_label(
    original: str,
    primary: Optional[str],
    fallback: Optional[str],
    bilingual: bool,
) -> str:
    values = [v for v in (primary, fallback if bilingual else None) if v]
    if not values:
        return original
    if bilingual and len(values) == 2 and values[0] != values[1]:
        return f"{values[0]} ({values[1]})"
    return values[0]


def entity_label(
    i18n: I18nDicts,
    domain: str,
    name: str,
    primary_lang: str,
    fallback_lang: str,
    bilingual: bool,
) -> str:
    key_primary = (domain, name, primary_lang)
    key_fallback = (domain, name, fallback_lang)
    primary = i18n.entities.get(key_primary)
    fallback = i18n.entities.get(key_fallback)
    return _compose_label(name, primary, fallback, bilingual)


def attr_label(
    i18n: I18nDicts,
    domain: str,
    entity: str,
    attr: str,
    primary_lang: str,
    fallback_lang: str,
    bilingual: bool,
) -> str:
    key_primary = (domain, entity, attr, primary_lang)
    key_fallback = (domain, entity, attr, fallback_lang)
    primary = i18n.attributes.get(key_primary)
    fallback = i18n.attributes.get(key_fallback)
    return _compose_label(attr, primary, fallback, bilingual)
