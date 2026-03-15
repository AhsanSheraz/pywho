"""Tests for the scan formatter."""

from __future__ import annotations

from pathlib import Path

from pywho.scan_formatter import format_scan
from pywho.scanner import Severity, ShadowResult


def _shadow(path: str, name: str, shadows: str, severity: Severity) -> ShadowResult:
    return ShadowResult(
        path=Path(path),
        module_name=name,
        shadows=shadows,
        severity=severity,
    )


class TestScanFormatter:
    """Test terminal formatting of scan results."""

    def test_format_no_shadows(self) -> None:
        output = format_scan([], Path("/project"))
        assert "No shadows detected" in output

    def test_format_high_severity(self) -> None:
        results = [_shadow("/project/math.py", "math", "stdlib", Severity.HIGH)]
        output = format_scan(results, Path("/project"))
        assert "HIGH" in output
        assert "1 shadow(s)" in output

    def test_format_medium_severity(self) -> None:
        results = [
            _shadow("/project/requests.py", "requests", "installed:requests", Severity.MEDIUM),
        ]
        output = format_scan(results, Path("/project"))
        assert "MEDIUM" in output

    def test_format_mixed_severities(self) -> None:
        results = [
            _shadow("/project/math.py", "math", "stdlib", Severity.HIGH),
            _shadow("/project/requests.py", "requests", "installed:requests", Severity.MEDIUM),
        ]
        output = format_scan(results, Path("/project"))
        assert "HIGH" in output
        assert "MEDIUM" in output
        assert "2 shadow(s)" in output

    def test_format_path_outside_root(self) -> None:
        results = [_shadow("/other/math.py", "math", "stdlib", Severity.HIGH)]
        output = format_scan(results, Path("/project"))
        assert "math.py" in output
