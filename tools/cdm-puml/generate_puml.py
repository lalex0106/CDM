"""Executable entry point for the CDM PlantUML generator."""

from __future__ import annotations

import sys

from cdm_puml.cli import main


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
