"""Tests for the trace formatter."""

from __future__ import annotations

from pywho.trace_formatter import format_trace
from pywho.tracer import ModuleType, ShadowWarning, TraceReport, trace_import


class TestTraceFormatter:
    """Test terminal formatting of trace reports."""

    def test_format_contains_module_name(self) -> None:
        report = trace_import("json")
        output = format_trace(report)
        assert "json" in output

    def test_format_contains_resolved_path(self) -> None:
        report = trace_import("os")
        output = format_trace(report)
        assert "Resolved to" in output

    def test_format_not_found(self) -> None:
        report = trace_import("nonexistent_xyz_99999")
        output = format_trace(report)
        assert "NOT FOUND" in output

    def test_format_shows_search_order(self) -> None:
        report = trace_import("json", verbose=True)
        output = format_trace(report)
        assert "Search order" in output

    def test_format_returns_string(self) -> None:
        report = trace_import("os")
        output = format_trace(report)
        assert isinstance(output, str)
        assert len(output) > 50


class TestTraceFormatterEdgeCases:
    """Test formatting for edge cases."""

    def test_format_with_shadow_warnings(self) -> None:
        report = TraceReport(
            module_name="json",
            resolved_path="/tmp/json.py",
            module_type=ModuleType.LOCAL,
            is_package=False,
            is_cached=False,
            submodule_of=None,
            search_log=[],
            shadows=[
                ShadowWarning(
                    shadow_path="/tmp/json.py",
                    shadowed_module="json",
                    description="'/tmp/json.py' shadows stdlib module 'json'",
                ),
            ],
        )
        output = format_trace(report)
        assert "WARNING" in output

    def test_format_with_submodule(self) -> None:
        report = TraceReport(
            module_name="os.path",
            resolved_path="/usr/lib/python3.12/posixpath.py",
            module_type=ModuleType.STDLIB,
            is_package=False,
            is_cached=True,
            submodule_of="os",
            search_log=[],
            shadows=[],
        )
        output = format_trace(report)
        assert "Submodule of" in output
        assert "os" in output
