"""Tests for the terminal formatter."""

from __future__ import annotations

from pywho.formatter import format_report
from pywho.inspector import inspect_environment


class TestFormatter:
    """Test terminal output formatting."""

    def test_format_contains_sections(self) -> None:
        report = inspect_environment(include_packages=False)
        output = format_report(report)
        assert "Interpreter" in output
        assert "Platform" in output
        assert "Virtual Environment" in output
        assert "Paths" in output
        assert "sys.path" in output

    def test_format_with_packages(self) -> None:
        report = inspect_environment(include_packages=True)
        output = format_report(report, show_packages=True)
        assert "Installed Packages" in output

    def test_format_without_packages(self) -> None:
        report = inspect_environment(include_packages=False)
        output = format_report(report, show_packages=False)
        assert "Installed Packages" not in output

    def test_format_returns_string(self) -> None:
        report = inspect_environment(include_packages=False)
        output = format_report(report)
        assert isinstance(output, str)
        assert len(output) > 100  # Should have substantial content
