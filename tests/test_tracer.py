"""Tests for the import resolution tracer."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pywho.tracer import (
    ModuleType,
    PathSearchEntry,
    SearchResult,
    TraceReport,
    _classify_module,
    _detect_shadows,
    trace_import,
)


class TestTraceStdlib:
    """Test tracing stdlib modules."""

    def test_trace_os(self) -> None:
        report = trace_import("os")
        assert report.module_name == "os"
        assert report.resolved_path is not None
        assert report.module_type in (ModuleType.STDLIB, ModuleType.BUILTIN, ModuleType.FROZEN)

    def test_trace_json(self) -> None:
        report = trace_import("json")
        assert report.module_name == "json"
        assert report.resolved_path is not None
        assert report.is_package is True

    def test_trace_sys(self) -> None:
        report = trace_import("sys")
        assert report.module_name == "sys"
        assert report.module_type == ModuleType.BUILTIN

    def test_trace_os_path(self) -> None:
        report = trace_import("os.path")
        assert report.module_name == "os.path"
        assert report.submodule_of == "os"

    def test_trace_math(self) -> None:
        report = trace_import("math")
        assert report.module_name == "math"
        assert report.resolved_path is not None


class TestTraceThirdParty:
    """Test tracing installed third-party packages."""

    def test_trace_pytest(self) -> None:
        report = trace_import("pytest")
        assert report.module_name == "pytest"
        assert report.resolved_path is not None
        assert report.module_type == ModuleType.THIRD_PARTY
        assert report.is_package is True

    def test_trace_not_installed(self) -> None:
        report = trace_import("nonexistent_module_xyz_12345")
        assert report.module_type == ModuleType.NOT_FOUND
        assert report.resolved_path is None


class TestTraceShadows:
    """Test shadow detection."""

    def test_detects_stdlib_shadow(self, tmp_path: Path) -> None:
        shadow_file = tmp_path / "json.py"
        shadow_file.write_text("# shadow")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            report = trace_import("json")
            found = [e for e in report.search_log if e.result == SearchResult.FOUND]
            assert len(found) >= 2
            assert str(tmp_path) in found[0].path
        finally:
            sys.path[:] = original_path

    def test_no_shadow_for_clean_module(self) -> None:
        report = trace_import("os")
        stdlib_shadows = [s for s in report.shadows if "shadows stdlib" in s.description]
        assert len(stdlib_shadows) == 0


class TestTraceSearchLog:
    """Test the search log."""

    def test_search_log_not_empty(self) -> None:
        report = trace_import("os", verbose=True)
        assert len(report.search_log) > 0

    def test_verbose_includes_more_entries(self) -> None:
        brief = trace_import("json")
        verbose = trace_import("json", verbose=True)
        assert len(verbose.search_log) >= len(brief.search_log)

    def test_found_entry_has_candidate(self) -> None:
        report = trace_import("json", verbose=True)
        found = [e for e in report.search_log if e.result == SearchResult.FOUND]
        assert len(found) >= 1
        assert found[0].candidate is not None


class TestTraceCached:
    """Test cache detection."""

    def test_cached_module(self) -> None:
        report = trace_import("os")
        assert report.is_cached is True

    def test_uncached_module(self) -> None:
        mod_name = "pywho.tracer"
        original = sys.modules.pop(mod_name, None)
        try:
            report = trace_import(mod_name)
            assert report.is_cached is False
        finally:
            if original is not None:
                sys.modules[mod_name] = original


class TestTraceReport:
    """Test the TraceReport dataclass."""

    def test_to_dict(self) -> None:
        report = trace_import("os")
        d = report.to_dict()
        assert d["module_name"] == "os"
        assert "resolved_path" in d
        assert "module_type" in d
        assert "search_log" in d
        assert "shadows" in d

    def test_to_dict_json_serializable(self) -> None:
        report = trace_import("json", verbose=True)
        d = report.to_dict()
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


class TestClassifyModule:
    """Test module classification."""

    def test_classify_frozen_module(self) -> None:
        spec = MagicMock()
        spec.origin = "frozen"
        assert _classify_module("_frozen_importlib", spec) == ModuleType.FROZEN

    def test_classify_stdlib_by_name(self) -> None:
        spec = MagicMock()
        spec.origin = "/some/path/json/__init__.py"
        assert _classify_module("json", spec) in (ModuleType.STDLIB, ModuleType.LOCAL)


class TestDetectShadows:
    """Test shadow detection logic."""

    def test_no_shadow_with_single_found(self) -> None:
        log = [
            PathSearchEntry(path="/usr/lib/python3.12", result=SearchResult.FOUND, candidate="/usr/lib/python3.12/json/__init__.py"),
            PathSearchEntry(path="/tmp", result=SearchResult.NOT_FOUND),
        ]
        shadows = _detect_shadows("json", log, ModuleType.STDLIB)
        assert len(shadows) == 0

    def test_local_shadows_third_party(self) -> None:
        log = [
            PathSearchEntry(path="/project", result=SearchResult.FOUND, candidate="/project/requests.py"),
            PathSearchEntry(path="/usr/lib/python3.12/site-packages", result=SearchResult.FOUND, candidate="/usr/lib/python3.12/site-packages/requests/__init__.py"),
        ]
        shadows = _detect_shadows("requests", log, ModuleType.LOCAL)
        assert len(shadows) >= 1

    def test_find_spec_value_error(self) -> None:
        with patch("pywho.tracer.importlib.util.find_spec", side_effect=ValueError("bad")):
            report = trace_import("some.bad.module")
            assert report.module_type == ModuleType.NOT_FOUND
