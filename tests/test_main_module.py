"""Tests for python -m pywho."""

from __future__ import annotations

import subprocess
import sys


class TestMainModule:
    """Test running pywho as a module."""

    def test_run_as_module(self) -> None:
        """Test running pywho via 'python -m pywho'."""
        result = subprocess.run(
            [sys.executable, "-m", "pywho", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "interpreter" in result.stdout
