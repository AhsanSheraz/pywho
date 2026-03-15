"""Tests for the core environment inspector."""

from __future__ import annotations

import os
import platform
import sys

import pytest

from pywho.inspector import (
    EnvironmentReport,
    PackageInfo,
    VenvInfo,
    _detect_package_manager,
    _detect_venv,
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
        # Should have at least pip and pytest
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
            # Could still be conda
            if not os.environ.get("CONDA_DEFAULT_ENV"):
                assert venv.is_active is False


class TestSitePackages:
    """Test site-packages detection."""

    def test_returns_list(self) -> None:
        result = _get_site_packages()
        assert isinstance(result, list)


class TestPackageManager:
    """Test package manager detection."""

    def test_returns_string(self) -> None:
        result = _detect_package_manager()
        assert isinstance(result, str)
        assert result in ("pip", "conda", "pipenv", "poetry", "uv", "pyenv")


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
        # Should not raise
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
