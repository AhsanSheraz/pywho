"""Tests for the trace formatter."""

from __future__ import annotations

from pywho.trace_formatter import format_trace
from pywho.tracer import trace_import


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
