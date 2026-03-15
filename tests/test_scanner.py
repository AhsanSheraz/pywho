"""Tests for the project-wide shadow scanner."""

from __future__ import annotations

from pathlib import Path

import pytest

from pywho.scanner import Severity, ShadowResult, scan_path


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


class TestCLIIntegration:
    """Test scan via the CLI."""

    def test_scan_clean_dir(self, tmp_path: Path) -> None:
        from pywho.cli import main
        _create_file(tmp_path, "myapp.py")
        assert main(["scan", str(tmp_path), "--no-installed"]) == 0

    def test_scan_shadow_dir(self, tmp_path: Path) -> None:
        from pywho.cli import main
        _create_file(tmp_path, "math.py")
        assert main(["scan", str(tmp_path), "--no-installed"]) == 1

    def test_scan_json_output(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        import json
        from pywho.cli import main
        _create_file(tmp_path, "json.py")
        main(["scan", str(tmp_path), "--json", "--no-installed"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["module"] == "json"
        assert data[0]["severity"] == "high"

    def test_scan_nonexistent_path(self) -> None:
        from pywho.cli import main
        assert main(["scan", "/nonexistent/path/xyz"]) == 2
