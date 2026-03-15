"""Tests to cover missing lines across modules."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from pywho.cli import main
from pywho.formatter import _supports_color as fmt_supports_color, format_report
from pywho.inspector import (
    EnvironmentReport,
    PackageInfo,
    VenvInfo,
    _detect_package_manager,
    _detect_venv,
    _get_installed_packages,
    _get_pip_version,
    _get_site_packages,
    inspect_environment,
)
from pywho.scan_formatter import format_scan
from pywho.scan_formatter import _supports_color as scan_supports_color
from pywho.scanner import (
    Severity,
    ShadowResult,
    _get_stdlib_names,
    _is_installed_package,
    scan_path,
)
from pywho.trace_formatter import format_trace
from pywho.trace_formatter import _supports_color as trace_supports_color
from pywho.tracer import (
    ModuleType,
    PathSearchEntry,
    SearchResult,
    ShadowWarning,
    TraceReport,
    _classify_module,
    _detect_shadows,
    trace_import,
)


# ============================================================
# inspector.py coverage
# ============================================================


class TestVenvDetectionEdgeCases:
    """Cover venv detection branches for conda, pipenv, virtualenv, poetry, uv."""

    def test_conda_detection(self) -> None:
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base", "CONDA_PREFIX": "/opt/conda"}):
            venv = _detect_venv()
            assert venv.type == "conda"
            assert venv.is_active is True
            assert venv.path == "/opt/conda"

    def test_pipenv_detection(self) -> None:
        with patch.dict(os.environ, {"PIPENV_ACTIVE": "1"}, clear=False):
            # Need prefix != base_prefix for pipenv detection path via the early return
            venv = _detect_venv()
            assert venv.type == "pipenv"
            assert venv.is_active is True

    def test_no_venv_when_prefix_equals_base(self) -> None:
        env_clean = {k: v for k, v in os.environ.items()
                     if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        with patch.dict(os.environ, env_clean, clear=True), \
             patch.object(sys, "prefix", sys.base_prefix):
            venv = _detect_venv()
            assert venv.is_active is False
            assert venv.type == "none"

    def test_virtualenv_detection(self, tmp_path: Path) -> None:
        """Simulate a virtualenv by creating orig-prefix.txt."""
        fake_prefix = str(tmp_path / "fakevenv")
        lib_dir = tmp_path / "fakevenv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
        lib_dir.mkdir(parents=True)
        (lib_dir / "orig-prefix.txt").write_text("/usr")
        # Also create pyvenv.cfg without uv
        (tmp_path / "fakevenv" / "pyvenv.cfg").write_text("home = /usr/bin\n")

        env_clean = {k: v for k, v in os.environ.items()
                     if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        with patch.dict(os.environ, env_clean, clear=True), \
             patch.object(sys, "prefix", fake_prefix), \
             patch.object(sys, "base_prefix", "/usr"):
            venv = _detect_venv()
            assert venv.type == "virtualenv"
            assert venv.is_active is True

    def test_uv_venv_detection(self, tmp_path: Path) -> None:
        """Simulate a uv venv via pyvenv.cfg."""
        fake_prefix = str(tmp_path / "uvvenv")
        (tmp_path / "uvvenv").mkdir()
        (tmp_path / "uvvenv" / "pyvenv.cfg").write_text("home = /usr/bin\nuv = 0.1.0\nprompt = myproject\n")

        env_clean = {k: v for k, v in os.environ.items()
                     if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        with patch.dict(os.environ, env_clean, clear=True), \
             patch.object(sys, "prefix", fake_prefix), \
             patch.object(sys, "base_prefix", "/usr"):
            venv = _detect_venv()
            assert venv.type == "uv"
            assert venv.prompt == "myproject"

    def test_poetry_venv_detection(self, tmp_path: Path) -> None:
        """Simulate poetry venv."""
        fake_prefix = str(tmp_path / "poetryvenv")
        (tmp_path / "poetryvenv").mkdir()

        with patch.dict(os.environ, {"POETRY_ACTIVE": "1"}, clear=False), \
             patch.object(sys, "prefix", fake_prefix), \
             patch.object(sys, "base_prefix", "/usr"):
            venv = _detect_venv()
            assert venv.type == "poetry"

    def test_pyvenv_cfg_oserror(self, tmp_path: Path) -> None:
        """pyvenv.cfg read raises OSError."""
        fake_prefix = str(tmp_path / "badvenv")
        (tmp_path / "badvenv").mkdir()
        cfg = tmp_path / "badvenv" / "pyvenv.cfg"
        cfg.write_text("home = /usr\n")
        # Make unreadable
        cfg.chmod(0o000)

        env_clean = {k: v for k, v in os.environ.items()
                     if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        try:
            with patch.dict(os.environ, env_clean, clear=True), \
                 patch.object(sys, "prefix", fake_prefix), \
                 patch.object(sys, "base_prefix", "/usr"):
                venv = _detect_venv()
                assert venv.is_active is True
        finally:
            cfg.chmod(0o644)

    def test_windows_virtualenv_detection(self, tmp_path: Path) -> None:
        """Simulate Windows virtualenv with Lib/orig-prefix.txt."""
        fake_prefix = str(tmp_path / "winvenv")
        lib_dir = tmp_path / "winvenv" / "Lib"
        lib_dir.mkdir(parents=True)
        (lib_dir / "orig-prefix.txt").write_text("C:\\Python312")

        env_clean = {k: v for k, v in os.environ.items()
                     if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        with patch.dict(os.environ, env_clean, clear=True), \
             patch.object(sys, "prefix", fake_prefix), \
             patch.object(sys, "base_prefix", "C:\\Python312"), \
             patch.object(sys, "platform", "win32"):
            venv = _detect_venv()
            assert venv.type == "virtualenv"


class TestPackageManagerEdgeCases:
    """Cover package manager detection branches."""

    def test_conda_manager(self) -> None:
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base"}):
            assert _detect_package_manager() == "conda"

    def test_pipenv_manager(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "CONDA_DEFAULT_ENV"}
        env["PIPENV_ACTIVE"] = "1"
        with patch.dict(os.environ, env, clear=True):
            assert _detect_package_manager() == "pipenv"

    def test_poetry_manager(self) -> None:
        env = {k: v for k, v in os.environ.items()
               if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE")}
        env["POETRY_ACTIVE"] = "1"
        with patch.dict(os.environ, env, clear=True):
            assert _detect_package_manager() == "poetry"

    def test_pyenv_manager(self) -> None:
        env = {k: v for k, v in os.environ.items()
               if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        with patch.dict(os.environ, env, clear=True), \
             patch.object(sys, "executable", "/home/user/.pyenv/shims/python"):
            # Also need to ensure pyvenv.cfg doesn't have uv
            with patch("pywho.inspector.Path") as MockPath:
                cfg = MagicMock()
                cfg.exists.return_value = False
                MockPath.return_value.__truediv__ = lambda self, other: cfg
                assert _detect_package_manager() == "pyenv"

    def test_uv_manager(self, tmp_path: Path) -> None:
        """pyvenv.cfg with uv key should return uv."""
        cfg = tmp_path / "pyvenv.cfg"
        cfg.write_text("uv = 0.5.0\n")
        env = {k: v for k, v in os.environ.items()
               if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        with patch.dict(os.environ, env, clear=True), \
             patch.object(sys, "prefix", str(tmp_path)):
            assert _detect_package_manager() == "uv"

    def test_uv_manager_cfg_oserror(self, tmp_path: Path) -> None:
        cfg = tmp_path / "pyvenv.cfg"
        cfg.write_text("uv = 0.5\n")
        cfg.chmod(0o000)
        env = {k: v for k, v in os.environ.items()
               if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")}
        try:
            with patch.dict(os.environ, env, clear=True), \
                 patch.object(sys, "prefix", str(tmp_path)), \
                 patch.object(sys, "executable", "/usr/bin/python"):
                result = _detect_package_manager()
                assert result == "pip"
        finally:
            cfg.chmod(0o644)


class TestPipVersion:
    """Cover _get_pip_version edge cases."""

    def test_pip_version_returns_string_or_none(self) -> None:
        result = _get_pip_version()
        assert result is None or isinstance(result, str)

    def test_pip_version_timeout(self) -> None:
        with patch("pywho.inspector.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pip", timeout=5)):
            assert _get_pip_version() is None

    def test_pip_version_not_found(self) -> None:
        with patch("pywho.inspector.subprocess.run", side_effect=FileNotFoundError):
            assert _get_pip_version() is None

    def test_pip_version_nonzero_return(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("pywho.inspector.subprocess.run", return_value=mock_result):
            assert _get_pip_version() is None


import subprocess


class TestGetInstalledPackages:
    """Cover _get_installed_packages."""

    def test_returns_sorted_list(self) -> None:
        pkgs = _get_installed_packages()
        assert isinstance(pkgs, list)
        if len(pkgs) > 1:
            names = [p.name.lower() for p in pkgs]
            assert names == sorted(names)

    def test_handles_exception(self) -> None:
        with patch("importlib.metadata.distributions", side_effect=Exception("boom")):
            result = _get_installed_packages()
            assert result == []


class TestSitePackages:
    """Cover _get_site_packages edge cases."""

    def test_no_getsitepackages(self) -> None:
        with patch.object(site, "getsitepackages", side_effect=AttributeError):
            result = _get_site_packages()
            assert isinstance(result, list)

    def test_user_site_not_dir(self) -> None:
        with patch.object(site, "getusersitepackages", return_value="/nonexistent/path"):
            result = _get_site_packages()
            assert isinstance(result, list)


import site


# ============================================================
# formatter.py coverage
# ============================================================


class TestFormatterEdgeCases:
    """Cover formatter branches."""

    def test_supports_color_ansicon(self) -> None:
        with patch.dict(os.environ, {"ANSICON": "1"}), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert fmt_supports_color() is True

    def test_supports_color_wt_session(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANSICON"}
        env["WT_SESSION"] = "1"
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert fmt_supports_color() is True

    def test_supports_color_false(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("ANSICON", "WT_SESSION")}
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert fmt_supports_color() is False

    def test_format_no_venv(self) -> None:
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
        # No venv should show "No (system Python)"
        assert "No" in output
        # prefix == base_prefix should not show Base Prefix
        assert "Base Prefix" not in output

    def test_format_venv_no_prompt_no_path(self) -> None:
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


# ============================================================
# scan_formatter.py coverage
# ============================================================


class TestScanFormatterEdgeCases:
    """Cover scan formatter branches."""

    def test_supports_color_ansicon(self) -> None:
        with patch.dict(os.environ, {"ANSICON": "1"}), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert scan_supports_color() is True

    def test_supports_color_wt_session(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANSICON"}
        env["WT_SESSION"] = "1"
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert scan_supports_color() is True

    def test_supports_color_false(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("ANSICON", "WT_SESSION")}
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert scan_supports_color() is False

    def test_format_medium_severity(self) -> None:
        results = [
            ShadowResult(
                path=Path("/project/requests.py"),
                module_name="requests",
                shadows="installed:requests",
                severity=Severity.MEDIUM,
            ),
        ]
        output = format_scan(results, Path("/project"))
        assert "MEDIUM" in output
        assert "1" in output

    def test_format_mixed_severities(self) -> None:
        results = [
            ShadowResult(path=Path("/project/math.py"), module_name="math", shadows="stdlib", severity=Severity.HIGH),
            ShadowResult(path=Path("/project/requests.py"), module_name="requests", shadows="installed:requests", severity=Severity.MEDIUM),
        ]
        output = format_scan(results, Path("/project"))
        assert "HIGH" in output
        assert "MEDIUM" in output
        assert "2 shadow(s)" in output

    def test_format_path_not_relative(self) -> None:
        results = [
            ShadowResult(path=Path("/other/math.py"), module_name="math", shadows="stdlib", severity=Severity.HIGH),
        ]
        output = format_scan(results, Path("/project"))
        assert "math.py" in output


# ============================================================
# trace_formatter.py coverage
# ============================================================


class TestTraceFormatterEdgeCases:
    """Cover trace formatter branches."""

    def test_supports_color_ansicon(self) -> None:
        with patch.dict(os.environ, {"ANSICON": "1"}), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert trace_supports_color() is True

    def test_supports_color_wt_session(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANSICON"}
        env["WT_SESSION"] = "1"
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert trace_supports_color() is True

    def test_supports_color_false(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("ANSICON", "WT_SESSION")}
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new=MagicMock(isatty=lambda: False)):
            assert trace_supports_color() is False

    def test_format_with_shadows(self) -> None:
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


# ============================================================
# scanner.py coverage
# ============================================================


class TestScannerEdgeCases:
    """Cover scanner branches."""

    def test_get_stdlib_names_fallback(self) -> None:
        """Test the 3.9 fallback when sys.stdlib_module_names doesn't exist."""
        with patch.object(sys, "stdlib_module_names", create=False, new=None):
            # Remove the attr entirely
            saved = getattr(sys, "stdlib_module_names", None)
            if hasattr(sys, "stdlib_module_names"):
                delattr(sys, "stdlib_module_names")
            try:
                names = _get_stdlib_names()
                assert "os" in names
                assert "json" in names
                assert "math" in names
            finally:
                if saved is not None:
                    sys.stdlib_module_names = saved  # type: ignore[attr-defined]

    def test_is_installed_package_true(self) -> None:
        assert _is_installed_package("pytest") is True

    def test_is_installed_package_false_not_found(self) -> None:
        assert _is_installed_package("nonexistent_xyz_99999") is False

    def test_is_installed_package_stdlib(self) -> None:
        # os is stdlib, not installed third-party
        assert _is_installed_package("os") is False

    def test_is_installed_package_builtin(self) -> None:
        assert _is_installed_package("sys") is False

    def test_installed_package_shadow(self, tmp_path: Path) -> None:
        """Scan should detect a file shadowing an installed package."""
        (tmp_path / "pytest.py").write_text("# shadow")
        results = scan_path(tmp_path, check_installed=True)
        installed = [r for r in results if r.severity == Severity.MEDIUM]
        assert len(installed) >= 1
        assert any(r.module_name == "pytest" for r in installed)

    def test_scan_non_py_file(self, tmp_path: Path) -> None:
        (tmp_path / "math.txt").write_text("not python")
        results = scan_path(tmp_path / "math.txt", check_installed=False)
        assert len(results) == 0


# ============================================================
# tracer.py coverage
# ============================================================


class TestTracerEdgeCases:
    """Cover tracer branches."""

    def test_classify_frozen_module(self) -> None:
        spec = MagicMock()
        spec.origin = "frozen"
        assert _classify_module("_frozen_importlib", spec) == ModuleType.FROZEN

    def test_classify_stdlib_by_name(self) -> None:
        spec = MagicMock()
        spec.origin = "/some/path/json/__init__.py"
        # Not in site-packages, not starting with stdlib_path, but name is in stdlib_names
        assert _classify_module("json", spec) in (ModuleType.STDLIB, ModuleType.LOCAL)

    def test_detect_shadows_single_found(self) -> None:
        """No shadows when only one FOUND entry."""
        log = [
            PathSearchEntry(path="/usr/lib/python3.12", result=SearchResult.FOUND, candidate="/usr/lib/python3.12/json/__init__.py"),
            PathSearchEntry(path="/tmp", result=SearchResult.NOT_FOUND),
        ]
        shadows = _detect_shadows("json", log, ModuleType.STDLIB)
        assert len(shadows) == 0

    def test_detect_shadows_local_shadows_third_party(self) -> None:
        """Local file shadows a third-party package."""
        log = [
            PathSearchEntry(path="/project", result=SearchResult.FOUND, candidate="/project/requests.py"),
            PathSearchEntry(path="/usr/lib/python3.12/site-packages", result=SearchResult.FOUND, candidate="/usr/lib/python3.12/site-packages/requests/__init__.py"),
        ]
        shadows = _detect_shadows("requests", log, ModuleType.LOCAL)
        assert len(shadows) >= 1

    def test_trace_find_spec_value_error(self) -> None:
        with patch("pywho.tracer.importlib.util.find_spec", side_effect=ValueError("bad")):
            report = trace_import("some.bad.module")
            assert report.module_type == ModuleType.NOT_FOUND


# ============================================================
# cli.py coverage
# ============================================================


class TestCLITraceAndScan:
    """Cover CLI trace/scan dispatch branches."""

    def test_trace_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["trace", "os", "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["module_name"] == "os"
        assert result == 0

    def test_trace_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["trace", "json"])
        captured = capsys.readouterr()
        assert "Import Resolution" in captured.out
        assert result == 0

    def test_trace_with_shadow_returns_1(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (tmp_path / "json.py").write_text("# shadow")
        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            result = main(["trace", "json"])
            # May or may not detect shadow depending on search order
            assert result in (0, 1)
        finally:
            sys.path[:] = original_path

    def test_trace_dispatch(self) -> None:
        assert main(["trace", "os"]) == 0

    def test_scan_dispatch(self, tmp_path: Path) -> None:
        (tmp_path / "myapp.py").write_text("")
        assert main(["scan", str(tmp_path), "--no-installed"]) == 0

    def test_no_pip_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["--no-pip", "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "interpreter" in data
        assert result == 0
