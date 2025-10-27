"""Compatibility entry point wrapping :mod:`cdm_puml.cli`.

This thin wrapper mirrors the behaviour of ``samples/plantuml/generate_plantuml.py``
so that existing scripts can be migrated without rewriting their invocation.  When
the legacy positional arguments (``manifest`` and ``--entities``) are supplied they
are translated to the richer ``cdm_puml`` command line interface.  All other
arguments are forwarded as-is to :func:`cdm_puml.cli.main`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence

from cdm_puml import cli


def _build_compat_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("manifest", nargs="?", help="Path to the manifest file")
    parser.add_argument(
        "--entities",
        nargs="*",
        help="Legacy alias for --resources; entity names to traverse",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Legacy alias for the PlantUML output file",
    )
    return parser


def _ensure_option(
    forwarded: list[str],
    flag: str,
    values: Iterable[str] | None,
) -> None:
    if not values:
        return
    try:
        index = forwarded.index(flag)
    except ValueError:
        index = -1
    if index != -1:
        return
    forwarded.append(flag)
    forwarded.extend(str(value) for value in values)


def _translate_legacy_args(argv: Sequence[str]) -> list[str]:
    parser = _build_compat_parser()
    known, remainder = parser.parse_known_args(argv)
    forwarded = list(remainder)
    if known.manifest:
        _ensure_option(forwarded, "--manifest", [known.manifest])
    if known.entities:
        _ensure_option(forwarded, "--resources", known.entities)
    if known.output:
        _ensure_option(forwarded, "--output", [known.output])
    return forwarded


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in {"-h", "--help"} for arg in args):
        return cli.main(args)
    forwarded = _translate_legacy_args(args)
    return cli.main(forwarded)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
