"""Tests for the terminal formatter."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from pywho.formatter import _supports_color, format_report
from pywho.inspector import EnvironmentReport, VenvInfo, inspect_environment


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
        assert len(output) > 100


class TestFormatterColor:
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


class TestFormatterVenvBranches:
    """Test formatting for different venv states."""

    def test_format_inactive_venv(self) -> None:
        report = EnvironmentReport(
            executable="/usr/bin/python3",
            version="3.12.0",
            version_info="3.12.0",
            implementation="CPython",
            compiler="GCC",
            architecture="64-bit",
            build_date="",
            platform_system="Linux",
            platform_release="6.0",
            platform_machine="x86_64",
            venv=VenvInfo(is_active=False, type="none", path=None, prompt=None),
            prefix="/usr",
            base_prefix="/usr",
            exec_prefix="/usr",
            sys_path=["/usr/lib/python3.12", ""],
            site_packages=["/usr/lib/python3.12/site-packages"],
            package_manager="pip",
            pip_version=None,
            packages=[],
        )
        output = format_report(report)
        assert "No" in output
        assert "Base Prefix" not in output

    def test_format_active_venv_without_path_and_prompt(self) -> None:
        report = EnvironmentReport(
            executable="/usr/bin/python3",
            version="3.12.0",
            version_info="3.12.0",
            implementation="CPython",
            compiler="GCC",
            architecture="64-bit",
            build_date="",
            platform_system="Linux",
            platform_release="6.0",
            platform_machine="x86_64",
            venv=VenvInfo(is_active=True, type="venv", path=None, prompt=None),
            prefix="/home/user/.venv",
            base_prefix="/usr",
            exec_prefix="/usr",
            sys_path=[],
            site_packages=[],
            package_manager="pip",
            pip_version="24.0",
            packages=[],
        )
        output = format_report(report)
        assert "Active" in output
        assert "Base Prefix" in output
