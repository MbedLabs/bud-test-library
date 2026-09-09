"""Collect the Bloom test cases a suite claims, and find what is wrong with them."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from budtestlibrary.budtestcase import BudTestCase


@dataclass(frozen=True)
class TestClassRef:
    """A discovered test class and where it lives."""

    name: str
    module: str
    path: str
    tc_id: str | None

    def location(self) -> str:
        return f"{self.path}::{self.name}"


@dataclass
class TraceabilityReport:
    """What a suite claims about Bloom, and what does not hold."""

    traced: dict[str, list[TestClassRef]] = field(default_factory=dict)
    untraced: list[TestClassRef] = field(default_factory=list)
    unreadable: list[tuple[str, str]] = field(default_factory=list)

    @property
    def duplicates(self) -> dict[str, list[TestClassRef]]:
        return {tc_id: refs for tc_id, refs in self.traced.items() if len(refs) > 1}

    @property
    def ok(self) -> bool:
        return not self.duplicates and not self.unreadable

    def to_dict(self) -> dict:
        return {
            "traced": {
                tc_id: [ref.location() for ref in refs]
                for tc_id, refs in sorted(self.traced.items())
            },
            "duplicates": {
                tc_id: [ref.location() for ref in refs]
                for tc_id, refs in sorted(self.duplicates.items())
            },
            "untraced": [ref.location() for ref in self.untraced],
            "unreadable": [{"path": path, "error": error} for path, error in self.unreadable],
            "ok": self.ok,
        }


def _module_files(root: Path) -> Iterator[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*.py")):
        if path.name.startswith(".") or "__pycache__" in path.parts:
            continue
        yield path


def _load(path: Path):
    module_name = f"_budtestlibrary_check_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module


def collect(root: Path) -> TraceabilityReport:
    """Import every module under ``root`` and read the Bloom ids its tests claim."""

    report = TraceabilityReport()
    traced: dict[str, list[TestClassRef]] = defaultdict(list)

    for path in _module_files(root):
        try:
            module = _load(path)
        except Exception as exc:
            report.unreadable.append((str(path), f"{type(exc).__name__}: {exc}"))
            continue

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, BudTestCase) or obj is BudTestCase:
                continue
            if obj.__module__ != module.__name__:
                continue

            metadata = getattr(obj, "bloom_metadata", None)
            tc_id = metadata.get_full_tc_id() if hasattr(metadata, "get_full_tc_id") else None
            ref = TestClassRef(name=name, module=module.__name__, path=str(path), tc_id=tc_id)
            if tc_id is None:
                report.untraced.append(ref)
            else:
                traced[tc_id].append(ref)

    report.traced = dict(traced)
    return report
