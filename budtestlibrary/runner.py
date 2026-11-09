"""Run the BudTestCase suites of a file or a folder: ``python -m budtestlibrary run <path>``.

Each matching module is imported by its dotted name from the current directory, its neighbours
importable by package name, and every BudTestCase class the module itself defines runs in the
same process.
"""

from __future__ import annotations

import importlib
import inspect
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from budtestlibrary.budtestcase import BudTestCase


@dataclass
class RunReport:
    """The suites a run executed, the ones that failed and the modules that could not be imported."""

    ran: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    unreadable: list[tuple[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when at least one suite ran and nothing failed or was unreadable."""
        return bool(self.ran) and not self.failed and not self.unreadable


def module_files(path: Path, pattern: str) -> list[Path]:
    """The file itself, or the folder's files matching the pattern, without names starting with _
    or ., in name order."""
    if path.is_file():
        return [path]
    return sorted(
        candidate
        for candidate in path.glob(pattern)
        if candidate.is_file()
        and candidate.suffix == ".py"
        and not candidate.name.startswith(("_", "."))
    )


def module_name(path: Path, root: Path) -> str:
    """The dotted name of a module file below the root directory."""
    relative = path.resolve().relative_to(root.resolve())
    return ".".join(relative.with_suffix("").parts)


def suites_of(module) -> list[type[BudTestCase]]:
    """The BudTestCase classes the module itself defines, in name order."""
    return [
        member
        for _, member in inspect.getmembers(module, inspect.isclass)
        if member.__module__ == module.__name__
        and issubclass(member, BudTestCase)
        and member is not BudTestCase
    ]


def run(path: Path, pattern: str = "*.py", root: Path | None = None) -> RunReport:
    """Import each matching module below the root, the current directory by default, and run
    every BudTestCase class it defines."""
    root = (root or Path.cwd()).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    report = RunReport()
    for file in module_files(path, pattern):
        name = module_name(file, root)
        try:
            module = importlib.import_module(name)
        except Exception:
            report.unreadable.append((name, traceback.format_exc()))
            continue
        for suite in suites_of(module):
            label = f"{name}.{suite.__name__}"
            report.ran.append(label)
            try:
                passed = suite().run()
            except Exception:
                traceback.print_exc()
                passed = False
            if not passed:
                report.failed.append(label)
    return report


def render(report: RunReport, path: Path) -> str:
    """The run's summary: the count, then each failed suite and each module that could not be
    imported with its error."""
    lines = [f"{len(report.ran)} suite(s) ran in {path}, {len(report.failed)} failed"]
    lines.extend(f"FAILED {label}" for label in report.failed)
    for name, error in report.unreadable:
        lines.append(f"NOT IMPORTED {name}")
        lines.append(error.rstrip())
    if not report.ran and not report.unreadable:
        lines.append(f"no BudTestCase suite found in {path}")
    return "\n".join(lines)
