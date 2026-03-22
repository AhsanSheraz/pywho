"""Tests for the shared terminal utilities."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from pywho._terminal import colorize, supports_color


class TestSupportsColor:
    """Test ANSI color support detection."""

    def setup_method(self) -> None:
        supports_color.cache_clear()

    def teardown_method(self) -> None:
        supports_color.cache_clear()

    def test_tty_returns_true(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("NO_COLOR", "FORCE_COLOR")}
        with (
            patch.dict(os.environ, env, clear=True),
            patch("sys.stdout", new=MagicMock(isatty=lambda: True)),
        ):
            assert supports_color() is True

    def test_ansicon_returns_true(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("NO_COLOR", "FORCE_COLOR")}
        env["ANSICON"] = "1"
        with (
            patch.dict(os.environ, env, clear=True),
            patch("sys.stdout", new=MagicMock(isatty=lambda: False)),
        ):
            assert supports_color() is True

    def test_wt_session_returns_true(self) -> None:
        exclude = ("ANSICON", "NO_COLOR", "FORCE_COLOR")
        env = {k: v for k, v in os.environ.items() if k not in exclude}
        env["WT_SESSION"] = "1"
        with (
            patch.dict(os.environ, env, clear=True),
            patch("sys.stdout", new=MagicMock(isatty=lambda: False)),
        ):
            assert supports_color() is True

    def test_no_terminal_returns_false(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("ANSICON", "WT_SESSION", "NO_COLOR", "FORCE_COLOR")
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("sys.stdout", new=MagicMock(isatty=lambda: False)),
        ):
            assert supports_color() is False

    def test_no_color_disables_colors(self) -> None:
        with (
            patch.dict(os.environ, {"NO_COLOR": "1"}),
            patch("sys.stdout", new=MagicMock(isatty=lambda: True)),
        ):
            assert supports_color() is False

    def test_force_color_enables_colors(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "NO_COLOR"}
        env["FORCE_COLOR"] = "1"
        with (
            patch.dict(os.environ, env, clear=True),
            patch("sys.stdout", new=MagicMock(isatty=lambda: False)),
        ):
            assert supports_color() is True

    def test_no_color_takes_precedence_over_force_color(self) -> None:
        with (
            patch.dict(os.environ, {"NO_COLOR": "1", "FORCE_COLOR": "1"}),
            patch("sys.stdout", new=MagicMock(isatty=lambda: True)),
        ):
            assert supports_color() is False


class TestColorize:
    """Test text colorization."""

    def test_colorize_with_color_support(self) -> None:
        with patch("pywho._terminal.supports_color", return_value=True):
            result = colorize("hello", "\033[32m")
            assert "\033[32m" in result
            assert "hello" in result
            assert "\033[0m" in result

    def test_colorize_without_color_support(self) -> None:
        with patch("pywho._terminal.supports_color", return_value=False):
            result = colorize("hello", "\033[32m")
            assert result == "hello"
