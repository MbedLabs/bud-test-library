"""Command line entry point: ``python -m budtestlibrary check <path>``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from budtestlibrary.traceability import TraceabilityReport, collect


def _render(report: TraceabilityReport, show_map: bool) -> str:
    lines: list[str] = []

    for tc_id, refs in sorted(report.duplicates.items()):
        lines.append(f"✗ {tc_id} is claimed by {len(refs)} test classes:")
        lines.extend(f"    {ref.location()}" for ref in refs)

    for path, error in report.unreadable:
        lines.append(f"✗ {path} could not be imported: {error}")

    if report.untraced:
        lines.append(f"! {len(report.untraced)} test class(es) claim no Bloom test case:")
        lines.extend(f"    {ref.location()}" for ref in report.untraced)

    if show_map and report.traced:
        lines.append("")
        lines.append("Bloom test cases this suite covers:")
        for tc_id, refs in sorted(report.traced.items()):
            lines.extend(f"  {tc_id}  {ref.location()}" for ref in refs)

    claimed = sum(len(refs) for refs in report.traced.values())
    total = claimed + len(report.untraced)
    lines.append("")
    lines.append(
        f"{total} test class(es): {claimed} claim {len(report.traced)} Bloom test case(s), "
        f"{len(report.untraced)} claim none, {len(report.duplicates)} id(s) duplicated."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="budtestlibrary")
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser(
        "check",
        help="Report the Bloom test cases a suite claims, and refuse duplicates.",
    )
    check.add_argument("path", type=Path, help="Test file or directory to inspect.")
    check.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    check.add_argument("--list", action="store_true", help="Print the tc_id to test class map.")
    check.add_argument(
        "--strict",
        action="store_true",
        help="Also fail when a test class claims no Bloom test case.",
    )

    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"✗ {args.path} does not exist", file=sys.stderr)
        return 2

    report = collect(args.path)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(_render(report, show_map=args.list))

    if not report.ok:
        return 1
    if args.strict and report.untraced:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
