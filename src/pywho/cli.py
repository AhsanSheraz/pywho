"""Command-line interface for pywho."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from pywho import __version__
from pywho.formatter import format_report
from pywho.inspector import inspect_environment
from pywho.trace_formatter import format_trace
from pywho.tracer import trace_import


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pywho",
        description="Explain your Python environment in one command.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- trace subcommand ---
    trace_parser = subparsers.add_parser(
        "trace",
        help="Trace where an import resolves and why.",
    )
    trace_parser.add_argument(
        "module",
        help="Module name to trace (e.g., requests, json, os.path).",
    )
    trace_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show all sys.path entries, including skipped ones.",
    )
    trace_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON.",
    )

    # --- top-level flags (for default env report) ---
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


def _run_trace(args: argparse.Namespace) -> int:
    """Handle the 'trace' subcommand."""
    report = trace_import(args.module, verbose=args.verbose)

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_trace(report))

    # Exit 1 if shadows detected, 0 otherwise
    return 1 if report.shadows else 0


def _run_inspect(args: argparse.Namespace) -> int:
    """Handle the default environment inspection."""
    report = inspect_environment(include_packages=args.packages)

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report(report, show_packages=args.packages))

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "trace":
        return _run_trace(args)

    return _run_inspect(args)


if __name__ == "__main__":
    raise SystemExit(main())
