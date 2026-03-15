"""Tests for the CLI."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

import pytest

from pywho.cli import main

if TYPE_CHECKING:
    from pathlib import Path


class TestCLI:
    """Test the command-line interface."""

    def test_default_exit_zero(self) -> None:
        assert main([]) == 0

    def test_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "interpreter" in data
        assert "platform" in data
        assert "venv" in data
        assert "paths" in data

    def test_json_with_packages(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--json", "--packages"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data["packages"], list)
        assert len(data["packages"]) > 0

    def test_version(self) -> None:
        with pytest.raises(SystemExit, match="0"):
            main(["--version"])

    def test_text_output_contains_executable(self, capsys: pytest.CaptureFixture[str]) -> None:
        main([])
        captured = capsys.readouterr()
        assert "Executable" in captured.out
        assert "python" in captured.out.lower()

    def test_packages_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--packages"])
        captured = capsys.readouterr()
        assert "Installed Packages" in captured.out

    def test_no_pip_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["--no-pip", "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "interpreter" in data
        assert result == 0


class TestCLITrace:
    """Test the trace subcommand via CLI."""

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

    def test_trace_with_shadow_returns_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "json.py").write_text("# shadow")
        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            result = main(["trace", "json"])
            assert result in (0, 1)
        finally:
            sys.path[:] = original_path

    def test_trace_dispatch(self) -> None:
        assert main(["trace", "os"]) == 0


class TestCLIScan:
    """Test the scan subcommand via CLI."""

    def test_scan_clean_directory(self, tmp_path: Path) -> None:
        (tmp_path / "myapp.py").write_text("")
        assert main(["scan", str(tmp_path), "--no-installed"]) == 0

    def test_scan_shadow_directory(self, tmp_path: Path) -> None:
        (tmp_path / "math.py").write_text("")
        assert main(["scan", str(tmp_path), "--no-installed"]) == 1

    def test_scan_json_output(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (tmp_path / "json.py").write_text("")
        main(["scan", str(tmp_path), "--json", "--no-installed"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["module"] == "json"
        assert data[0]["severity"] == "high"

    def test_scan_nonexistent_path(self) -> None:
        assert main(["scan", "/nonexistent/path/xyz"]) == 2
