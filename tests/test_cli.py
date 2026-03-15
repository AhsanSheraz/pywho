"""Tests for the CLI."""

from __future__ import annotations

import json

import pytest

from pywho.cli import main


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
