"""Command-line interface for pywho."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from pywho import __version__
from pywho.formatter import format_report
from pywho.inspector import inspect_environment


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pywho",
        description="Explain your Python environment in one command.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON (for scripting, CI, or sharing).",
    )
    parser.add_argument(
        "--packages", "-p",
        action="store_true",
        help="Include list of all installed packages.",
    )
    parser.add_argument(
        "--no-pip",
        action="store_true",
        help="Skip pip version detection (faster).",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"pywho {__version__}",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    report = inspect_environment(include_packages=args.packages)

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report(report, show_packages=args.packages))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
