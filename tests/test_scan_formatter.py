"""Tests for the scan formatter."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from pywho.scan_formatter import _supports_color, format_scan
from pywho.scanner import Severity, ShadowResult


class TestScanFormatter:
    """Test terminal formatting of scan results."""

    def test_format_no_shadows(self) -> None:
        output = format_scan([], Path("/project"))
        assert "No shadows detected" in output

    def test_format_high_severity(self) -> None:
        results = [
            ShadowResult(path=Path("/project/math.py"), module_name="math", shadows="stdlib", severity=Severity.HIGH),
        ]
        output = format_scan(results, Path("/project"))
        assert "HIGH" in output
        assert "1 shadow(s)" in output

    def test_format_medium_severity(self) -> None:
        results = [
            ShadowResult(path=Path("/project/requests.py"), module_name="requests", shadows="installed:requests", severity=Severity.MEDIUM),
        ]
        output = format_scan(results, Path("/project"))
        assert "MEDIUM" in output

    def test_format_mixed_severities(self) -> None:
        results = [
            ShadowResult(path=Path("/project/math.py"), module_name="math", shadows="stdlib", severity=Severity.HIGH),
            ShadowResult(path=Path("/project/requests.py"), module_name="requests", shadows="installed:requests", severity=Severity.MEDIUM),
        ]
        output = format_scan(results, Path("/project"))
        assert "HIGH" in output
        assert "MEDIUM" in output
        assert "2 shadow(s)" in output

    def test_format_path_outside_root(self) -> None:
        results = [
            ShadowResult(path=Path("/other/math.py"), module_name="math", shadows="stdlib", severity=Severity.HIGH),
        ]
        output = format_scan(results, Path("/project"))
        assert "math.py" in output


class TestScanFormatterColor:
    """Test ANSI color support detection."""

    def test_supports_color_with_ansicon(self) -> None:
        with patch.dict(os.environ, {"ANSICON": "1"}), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert _supports_color() is True

    def test_supports_color_with_wt_session(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANSICON"}
        env["WT_SESSION"] = "1"
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert _supports_color() is True

    def test_supports_color_returns_false(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("ANSICON", "WT_SESSION")}
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert _supports_color() is False
