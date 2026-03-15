"""Tests for the project-wide shadow scanner."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from pywho.scanner import (
    Severity,
    ShadowResult,
    _get_stdlib_names,
    _is_installed_package,
    scan_path,
)


def _create_file(directory: Path, name: str, content: str = "") -> Path:
    filepath = directory / name
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)
    return filepath


class TestStdlibShadows:
    """Test detection of stdlib shadowing."""

    def test_detects_math_shadow(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "math.py", "# oops")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 1
        assert results[0].module_name == "math"
        assert results[0].severity == Severity.HIGH

    def test_detects_json_shadow(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "json.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 1
        assert results[0].module_name == "json"

    def test_detects_os_shadow(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "os.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 1
        assert results[0].module_name == "os"

    def test_detects_threading_shadow(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "threading.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 1
        assert results[0].module_name == "threading"

    def test_detects_package_shadow(self, tmp_path: Path) -> None:
        pkg = tmp_path / "logging"
        pkg.mkdir()
        _create_file(pkg, "__init__.py")
        results = scan_path(tmp_path, check_installed=False)
        assert any(r.module_name == "logging" for r in results)

    def test_multiple_shadows(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "math.py")
        _create_file(tmp_path, "json.py")
        _create_file(tmp_path, "os.py")
        results = scan_path(tmp_path, check_installed=False)
        names = {r.module_name for r in results}
        assert names == {"math", "json", "os"}


class TestNoFalsePositives:
    """Ensure common files are NOT flagged."""

    def test_ignores_setup_py(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "setup.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 0

    def test_ignores_conftest(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "conftest.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 0

    def test_ignores_private_modules(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "_helpers.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 0

    def test_ignores_normal_files(self, tmp_path: Path) -> None:
        _create_file(tmp_path, "myapp.py")
        _create_file(tmp_path, "utils.py")
        _create_file(tmp_path, "main.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 0

    def test_ignores_venv_directory(self, tmp_path: Path) -> None:
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        _create_file(venv, "os.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 0

    def test_ignores_pycache(self, tmp_path: Path) -> None:
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        _create_file(cache, "math.py")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 0


class TestSingleFile:
    """Test scanning a single file."""

    def test_single_shadow_file(self, tmp_path: Path) -> None:
        f = _create_file(tmp_path, "math.py")
        results = scan_path(f, check_installed=False)
        assert len(results) == 1

    def test_single_clean_file(self, tmp_path: Path) -> None:
        f = _create_file(tmp_path, "myapp.py")
        results = scan_path(f, check_installed=False)
        assert len(results) == 0

    def test_single_non_python_file(self, tmp_path: Path) -> None:
        f = _create_file(tmp_path, "math.txt", "not python")
        results = scan_path(f, check_installed=False)
        assert len(results) == 0


class TestShadowResult:
    """Test the ShadowResult dataclass."""

    def test_description_stdlib(self) -> None:
        r = ShadowResult(
            path=Path("math.py"),
            module_name="math",
            shadows="stdlib",
            severity=Severity.HIGH,
        )
        assert "stdlib" in r.description
        assert "math" in r.description

    def test_description_installed(self) -> None:
        r = ShadowResult(
            path=Path("requests.py"),
            module_name="requests",
            shadows="installed:requests",
            severity=Severity.MEDIUM,
        )
        assert "installed" in r.description


class TestStdlibNames:
    """Test stdlib name detection."""

    def test_stdlib_names_fallback(self) -> None:
        """Test the 3.9 fallback when sys.stdlib_module_names doesn't exist."""
        saved = getattr(sys, "stdlib_module_names", None)
        try:
            if hasattr(sys, "stdlib_module_names"):
                delattr(sys, "stdlib_module_names")
            names = _get_stdlib_names()
            assert "os" in names
            assert "json" in names
            assert "math" in names
        finally:
            if saved is not None:
                sys.stdlib_module_names = saved  # type: ignore[attr-defined]


class TestIsInstalledPackage:
    """Test installed package detection."""

    def test_installed_package_detected(self) -> None:
        assert _is_installed_package("pytest") is True

    def test_nonexistent_package_not_detected(self) -> None:
        assert _is_installed_package("nonexistent_xyz_99999") is False

    def test_stdlib_module_not_detected(self) -> None:
        assert _is_installed_package("os") is False

    def test_builtin_module_not_detected(self) -> None:
        assert _is_installed_package("sys") is False

    def test_value_error_returns_false(self) -> None:
        with patch("pywho.scanner.importlib.util.find_spec", side_effect=ValueError("bad")):
            assert _is_installed_package("badmod") is False

    def test_frozen_module_not_detected(self) -> None:
        mock_spec = MagicMock()
        mock_spec.origin = "frozen"
        with patch("pywho.scanner.importlib.util.find_spec", return_value=mock_spec):
            assert _is_installed_package("_frozen") is False


class TestScanPathOptions:
    """Test scan_path with custom options."""

    def test_custom_exclude_dirs(self, tmp_path: Path) -> None:
        mydir = tmp_path / "custom"
        mydir.mkdir()
        (mydir / "math.py").write_text("")
        results = scan_path(
            tmp_path,
            check_installed=False,
            exclude_dirs={"custom"},
        )
        assert len(results) == 0

    def test_custom_ignore_names(self, tmp_path: Path) -> None:
        (tmp_path / "math.py").write_text("")
        results = scan_path(
            tmp_path,
            check_installed=False,
            ignore_names={"math"},
        )
        assert len(results) == 0

    def test_egg_info_dirs_excluded(self, tmp_path: Path) -> None:
        egg_dir = tmp_path / "mypackage.egg-info"
        egg_dir.mkdir()
        (egg_dir / "math.py").write_text("")
        results = scan_path(tmp_path, check_installed=False)
        assert len(results) == 0

    def test_underscore_prefix_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "_thread.py").write_text("")
        results = scan_path(tmp_path, check_installed=False)
        # _thread is in stdlib so it should be detected (it's an exception)
        assert any(r.module_name == "_thread" for r in results)


class TestInstalledPackageShadow:
    """Test scanning for installed package shadows."""

    def test_detects_installed_package_shadow(self, tmp_path: Path) -> None:
        (tmp_path / "pytest.py").write_text("# shadow")
        results = scan_path(tmp_path, check_installed=True)
        installed = [r for r in results if r.severity == Severity.MEDIUM]
        assert len(installed) >= 1
        assert any(r.module_name == "pytest" for r in installed)
