"""Tests for the core environment inspector."""

from __future__ import annotations

import os
import platform
import site
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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


class TestInspectEnvironment:
    """Test the main inspection function."""

    def test_returns_report(self) -> None:
        report = inspect_environment(include_packages=False)
        assert isinstance(report, EnvironmentReport)

    def test_executable_matches_sys(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.executable == sys.executable

    def test_version_matches_platform(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.version == platform.python_version()

    def test_implementation(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.implementation == platform.python_implementation()

    def test_platform_system(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.platform_system == platform.system()

    def test_prefix_matches_sys(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.prefix == sys.prefix

    def test_base_prefix_matches_sys(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.base_prefix == sys.base_prefix

    def test_sys_path_is_list(self) -> None:
        report = inspect_environment(include_packages=False)
        assert isinstance(report.sys_path, list)
        assert len(report.sys_path) > 0

    def test_site_packages_is_list(self) -> None:
        report = inspect_environment(include_packages=False)
        assert isinstance(report.site_packages, list)

    def test_architecture_format(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.architecture in ("32-bit", "64-bit")

    def test_packages_included_when_requested(self) -> None:
        report = inspect_environment(include_packages=True)
        assert len(report.packages) > 0
        names = {p.name.lower() for p in report.packages}
        assert "pytest" in names

    def test_packages_empty_when_not_requested(self) -> None:
        report = inspect_environment(include_packages=False)
        assert report.packages == []


class TestVenvDetection:
    """Test virtual environment detection."""

    def test_detects_venv_status(self) -> None:
        venv = _detect_venv()
        assert isinstance(venv, VenvInfo)
        assert isinstance(venv.is_active, bool)

    def test_venv_type_is_string(self) -> None:
        venv = _detect_venv()
        assert venv.type in ("venv", "virtualenv", "conda", "poetry", "pipenv", "uv", "none")

    def test_venv_active_when_prefix_differs(self) -> None:
        venv = _detect_venv()
        if sys.prefix != sys.base_prefix:
            assert venv.is_active is True
        else:
            if not os.environ.get("CONDA_DEFAULT_ENV"):
                assert venv.is_active is False

    def test_conda_detection(self) -> None:
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base", "CONDA_PREFIX": "/opt/conda"}):
            venv = _detect_venv()
            assert venv.type == "conda"
            assert venv.is_active is True
            assert venv.path == "/opt/conda"

    def test_pipenv_detection(self) -> None:
        with patch.dict(os.environ, {"PIPENV_ACTIVE": "1"}, clear=False):
            venv = _detect_venv()
            assert venv.type == "pipenv"
            assert venv.is_active is True

    def test_no_venv_when_prefix_equals_base(self) -> None:
        env_clean = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env_clean, clear=True),
            patch.object(sys, "prefix", sys.base_prefix),
        ):
            venv = _detect_venv()
            assert venv.is_active is False
            assert venv.type == "none"

    def test_virtualenv_detection(self, tmp_path: Path) -> None:
        fake_prefix = str(tmp_path / "fakevenv")
        # Create orig-prefix.txt in both Unix and Windows locations
        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        unix_lib = tmp_path / "fakevenv" / "lib" / pyver
        unix_lib.mkdir(parents=True)
        (unix_lib / "orig-prefix.txt").write_text("/usr")
        win_lib = tmp_path / "fakevenv" / "Lib"
        win_lib.mkdir(parents=True, exist_ok=True)
        (win_lib / "orig-prefix.txt").write_text("/usr")
        (tmp_path / "fakevenv" / "pyvenv.cfg").write_text("home = /usr/bin\n")

        env_clean = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env_clean, clear=True),
            patch.object(sys, "prefix", fake_prefix),
            patch.object(sys, "base_prefix", "/usr"),
        ):
            venv = _detect_venv()
            assert venv.type == "virtualenv"
            assert venv.is_active is True

    def test_uv_venv_detection(self, tmp_path: Path) -> None:
        fake_prefix = str(tmp_path / "uvvenv")
        (tmp_path / "uvvenv").mkdir()
        cfg_text = "home = /usr/bin\nuv = 0.1.0\nprompt = myproject\n"
        (tmp_path / "uvvenv" / "pyvenv.cfg").write_text(cfg_text)

        env_clean = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env_clean, clear=True),
            patch.object(sys, "prefix", fake_prefix),
            patch.object(sys, "base_prefix", "/usr"),
        ):
            venv = _detect_venv()
            assert venv.type == "uv"
            assert venv.prompt == "myproject"

    def test_uv_venv_with_empty_prompt(self, tmp_path: Path) -> None:
        fake_prefix = str(tmp_path / "uvvenv2")
        (tmp_path / "uvvenv2").mkdir()
        cfg_text = "home = /usr/bin\nuv = 0.1.0\nprompt = \n"
        (tmp_path / "uvvenv2" / "pyvenv.cfg").write_text(cfg_text)

        env_clean = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env_clean, clear=True),
            patch.object(sys, "prefix", fake_prefix),
            patch.object(sys, "base_prefix", "/usr"),
        ):
            venv = _detect_venv()
            assert venv.type == "uv"
            assert venv.prompt == "uvvenv2"

    def test_win32_orig_prefix_path(self, tmp_path: Path) -> None:
        fake_prefix = str(tmp_path / "winvenv2")
        win_lib = tmp_path / "winvenv2" / "Lib"
        win_lib.mkdir(parents=True)
        (win_lib / "orig-prefix.txt").write_text("C:\\Python312")

        env_clean = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env_clean, clear=True),
            patch.object(sys, "prefix", fake_prefix),
            patch.object(sys, "base_prefix", "C:\\Python312"),
            patch.object(sys, "platform", "win32"),
        ):
            venv = _detect_venv()
            assert venv.type == "virtualenv"

    def test_poetry_venv_detection(self, tmp_path: Path) -> None:
        fake_prefix = str(tmp_path / "poetryvenv")
        (tmp_path / "poetryvenv").mkdir()

        with (
            patch.dict(os.environ, {"POETRY_ACTIVE": "1"}, clear=False),
            patch.object(sys, "prefix", fake_prefix),
            patch.object(sys, "base_prefix", "/usr"),
        ):
            venv = _detect_venv()
            assert venv.type == "poetry"

    def test_pyvenv_cfg_read_error(self, tmp_path: Path) -> None:
        fake_prefix = str(tmp_path / "badvenv")
        (tmp_path / "badvenv").mkdir()
        cfg = tmp_path / "badvenv" / "pyvenv.cfg"
        cfg.write_text("home = /usr\n")

        env_clean = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env_clean, clear=True),
            patch.object(sys, "prefix", fake_prefix),
            patch.object(sys, "base_prefix", "/usr"),
            patch.object(Path, "read_text", side_effect=OSError("permission denied")),
        ):
            venv = _detect_venv()
            assert venv.is_active is True

    def test_windows_virtualenv_detection(self, tmp_path: Path) -> None:
        fake_prefix = str(tmp_path / "winvenv")
        # Create both Unix and Windows orig-prefix.txt locations
        win_lib = tmp_path / "winvenv" / "Lib"
        win_lib.mkdir(parents=True)
        (win_lib / "orig-prefix.txt").write_text("C:\\Python312")
        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        unix_lib = tmp_path / "winvenv" / "lib" / pyver
        unix_lib.mkdir(parents=True)
        (unix_lib / "orig-prefix.txt").write_text("C:\\Python312")

        env_clean = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env_clean, clear=True),
            patch.object(sys, "prefix", fake_prefix),
            patch.object(sys, "base_prefix", "C:\\Python312"),
        ):
            venv = _detect_venv()
            assert venv.type == "virtualenv"


class TestSitePackages:
    """Test site-packages detection."""

    def test_returns_list(self) -> None:
        result = _get_site_packages()
        assert isinstance(result, list)

    def test_no_getsitepackages_attribute(self) -> None:
        with patch.object(site, "getsitepackages", side_effect=AttributeError):
            result = _get_site_packages()
            assert isinstance(result, list)

    def test_user_site_nonexistent_directory(self) -> None:
        with patch.object(site, "getusersitepackages", return_value="/nonexistent/path"):
            result = _get_site_packages()
            assert isinstance(result, list)


class TestPackageManager:
    """Test package manager detection."""

    def test_returns_string(self) -> None:
        result = _detect_package_manager()
        assert isinstance(result, str)
        assert result in ("pip", "conda", "pipenv", "poetry", "uv", "pyenv")

    def test_conda_manager(self) -> None:
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base"}):
            assert _detect_package_manager() == "conda"

    def test_pipenv_manager(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "CONDA_DEFAULT_ENV"}
        env["PIPENV_ACTIVE"] = "1"
        with patch.dict(os.environ, env, clear=True):
            assert _detect_package_manager() == "pipenv"

    def test_poetry_manager(self) -> None:
        env = {
            k: v for k, v in os.environ.items() if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE")
        }
        env["POETRY_ACTIVE"] = "1"
        with patch.dict(os.environ, env, clear=True):
            assert _detect_package_manager() == "poetry"

    def test_pyenv_manager(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(sys, "executable", "/home/user/.pyenv/shims/python"),
            patch("pywho.inspector.Path") as mock_path,
        ):
            cfg = MagicMock()
            cfg.exists.return_value = False
            mock_path.return_value.__truediv__ = lambda self, other: cfg
            assert _detect_package_manager() == "pyenv"

    def test_uv_manager(self, tmp_path: Path) -> None:
        cfg = tmp_path / "pyvenv.cfg"
        cfg.write_text("uv = 0.5.0\n")
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with patch.dict(os.environ, env, clear=True), patch.object(sys, "prefix", str(tmp_path)):
            assert _detect_package_manager() == "uv"

    def test_cfg_exists_but_no_uv(self, tmp_path: Path) -> None:
        cfg = tmp_path / "pyvenv.cfg"
        cfg.write_text("home = /usr/bin\n")
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(sys, "prefix", str(tmp_path)),
            patch.object(sys, "executable", "/usr/bin/python"),
        ):
            assert _detect_package_manager() == "pip"

    def test_uv_manager_cfg_read_error(self, tmp_path: Path) -> None:
        cfg = tmp_path / "pyvenv.cfg"
        cfg.write_text("uv = 0.5\n")
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CONDA_DEFAULT_ENV", "PIPENV_ACTIVE", "POETRY_ACTIVE")
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(sys, "prefix", str(tmp_path)),
            patch.object(sys, "executable", "/usr/bin/python"),
            patch.object(Path, "read_text", side_effect=OSError("permission denied")),
        ):
            assert _detect_package_manager() == "pip"


class TestPipVersion:
    """Test pip version detection."""

    def test_returns_string_or_none(self) -> None:
        result = _get_pip_version()
        assert result is None or isinstance(result, str)

    def test_timeout_returns_none(self) -> None:
        err = subprocess.TimeoutExpired(cmd="pip", timeout=5)
        with patch("pywho.inspector.subprocess.run", side_effect=err):
            assert _get_pip_version() is None

    def test_file_not_found_returns_none(self) -> None:
        with patch("pywho.inspector.subprocess.run", side_effect=FileNotFoundError):
            assert _get_pip_version() is None

    def test_nonzero_returncode_returns_none(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("pywho.inspector.subprocess.run", return_value=mock_result):
            assert _get_pip_version() is None

    def test_short_output_returns_none(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "pip"
        with patch("pywho.inspector.subprocess.run", return_value=mock_result):
            assert _get_pip_version() is None

    def test_oserror_returns_none(self) -> None:
        with patch("pywho.inspector.subprocess.run", side_effect=OSError("fail")):
            assert _get_pip_version() is None


class TestInstalledPackages:
    """Test installed packages listing."""

    def test_returns_sorted_list(self) -> None:
        pkgs = _get_installed_packages()
        assert isinstance(pkgs, list)
        if len(pkgs) > 1:
            names = [p.name.lower() for p in pkgs]
            assert names == sorted(names)

    def test_handles_exception(self) -> None:
        with patch("importlib.metadata.distributions", side_effect=Exception("boom")):
            assert _get_installed_packages() == []


class TestToDict:
    """Test serialization."""

    def test_to_dict_structure(self) -> None:
        report = inspect_environment(include_packages=False)
        d = report.to_dict()
        assert "interpreter" in d
        assert "platform" in d
        assert "venv" in d
        assert "paths" in d
        assert "package_manager" in d

    def test_to_dict_interpreter_fields(self) -> None:
        report = inspect_environment(include_packages=False)
        d = report.to_dict()
        interp = d["interpreter"]
        assert isinstance(interp, dict)
        assert "executable" in interp
        assert "version" in interp
        assert "implementation" in interp

    def test_to_dict_json_serializable(self) -> None:
        import json

        report = inspect_environment(include_packages=True)
        d = report.to_dict()
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


class TestPackageInfo:
    """Test the PackageInfo dataclass."""

    def test_creation(self) -> None:
        p = PackageInfo(name="foo", version="1.0.0", location="/path")
        assert p.name == "foo"
        assert p.version == "1.0.0"
        assert p.location == "/path"

    def test_frozen(self) -> None:
        p = PackageInfo(name="foo", version="1.0.0", location="/path")
        with pytest.raises(AttributeError):
            p.name = "bar"  # type: ignore[misc]
