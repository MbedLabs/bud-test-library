"""Shared steps of the budtestlibrary suites.

budtestlibrary can only be checked with itself: a step defines a small inner BudTestCase,
runs it with run() and reads what it recorded through get_results(), the console output it
wrote or the files it left. The outer step's own assertions go through the code under test,
so every comparison made with check() is also made in plain Python: a mismatch raises
RuntimeError, which fails the step whatever assertTrue records. Cases about the console
output or the exit code run a suite in a child process with the checkout on PYTHONPATH.

BUDTEST_WORK_DIR sets where the cases' files go (the system temporary directory otherwise).
"""

import io
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from budtestlibrary import BudTestCase

SUITES = Path(__file__).resolve().parent
REPO = SUITES.parent
PYTHON = sys.executable


def work_dir(name: str) -> Path:
    """Return a new empty directory for one case."""
    base = Path(os.environ.get("BUDTEST_WORK_DIR", tempfile.gettempdir()))
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{name}-", dir=base))


def _same(actual, expected) -> bool:
    """Return whether actual equals expected; None and booleans must be the same object."""
    if expected is None or isinstance(expected, bool):
        return actual is expected
    return not isinstance(actual, bool) and actual == expected


def check(case: BudTestCase, actual, expected, passed: str, failed: str = "") -> None:
    """Compare actual with expected first, then record one AssertEqual entry whose message says what happened.

    passed is the message when the values match and failed the message when they differ
    (passed is used for both while a suite has no failed message yet). The entry carries
    repr() of both values and the outcome decided here: a defect in the library's own
    comparison or recording leaves what the report shows unchanged. A mismatch also fails the
    step in plain Python.
    """
    same = _same(actual, expected)
    msg = passed if same else (failed or passed)
    case.assertTrue(
        same,
        msg=msg,
        expected=repr(expected),
        actual=repr(actual),
        assertion_type="AssertEqual",
    )
    if not same:
        text = f"{type(case).__name__}: {msg}: expected {expected!r}, got {actual!r}"
        raise RuntimeError(text)


def check_in(case: BudTestCase, member, container, passed: str, failed: str = "") -> None:
    """Look for member in container first, then record one AssertIn entry whose message says what happened."""
    found = member in container
    msg = passed if found else (failed or passed)
    case.assertIn(member=member, container=container, msg=msg)
    if not found:
        text = f"{type(case).__name__}: {msg}: {member!r} not in {container!r}"
        raise RuntimeError(text)


def check_not_in(case: BudTestCase, member, container, passed: str, failed: str = "") -> None:
    """Look for member in container first, then record one AssertNotIn entry whose message says what happened."""
    found = member in container
    msg = failed or passed if found else passed
    case.assertNotIn(member=member, container=container, msg=msg)
    if found:
        text = f"{type(case).__name__}: {msg}: {member!r} found in {container!r}"
        raise RuntimeError(text)


def raised(call, *args, **kwargs):
    """Call call(*args, **kwargs) and return the exception it raised, or None."""
    try:
        call(*args, **kwargs)
    except Exception as exc:
        return exc
    return None


def raised_name(exc) -> str:
    """Return the class name of exc, or 'nothing raised' when exc is None, for readable reports."""
    return "nothing raised" if exc is None else type(exc).__name__


def quiet(case: BudTestCase) -> BudTestCase:
    """Set case to log only critical lines and return it."""
    case.set_loglevel(logging.CRITICAL)
    return case


def run(case: BudTestCase, level: int = logging.CRITICAL):
    """Run case at the log level and return (what run() returned, get_results())."""
    case.set_loglevel(level)
    returned = case.run()
    return returned, case.get_results()


def run_capturing(case: BudTestCase, level: int = logging.INFO):
    """Run case with stderr replaced by a text buffer; return (returned, results, console text)."""
    saved = sys.stderr
    buffer = io.StringIO()
    sys.stderr = buffer
    try:
        returned, results = run(case, level)
    finally:
        sys.stderr = saved
    return returned, results, buffer.getvalue()


def step(body, **attributes):
    """Run an inner case whose only step bud_step calls body(case); return that step's result.

    attributes become class attributes of the inner case (CAPTURE_TRACEBACK and the like).
    """

    def bud_step(self):
        body(self)

    inner = type("InnerCase", (BudTestCase,), {"bud_step": bud_step, **attributes})
    return run(inner())[1][0]


class Done:
    """A finished child process: its exit code, stdout and stderr."""

    def __init__(self, code: int, out: str, err: str, raw_err: bytes = b""):
        self.code, self.out, self.err, self.raw_err = code, out, err, raw_err

    def __repr__(self) -> str:
        """Return the exit code and the ends of both outputs."""
        return f"exit {self.code}\n--- stdout\n{self.out[-3000:]}\n--- stderr\n{self.err[-3000:]}"


def child_env(extra: dict | None = None) -> dict:
    """Return the environment of a child: the checkout first on PYTHONPATH, no BUD_* setting."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("BUD_") and k != "PYTHONPATH"}
    env.update({"PYTHONPATH": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    for key, value in (extra or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = str(value)
    return env


def python(*args, env: dict | None = None, cwd: Path | None = None, timeout: float = 120) -> Done:
    """Run the suite's Python interpreter with the arguments and return its outcome."""
    done = subprocess.run(
        [PYTHON, *[str(a) for a in args]],
        cwd=str(cwd or work_dir("cwd")),
        env=child_env(env),
        capture_output=True,
        timeout=timeout,
    )
    out = done.stdout.decode("utf-8", errors="replace")
    err = done.stderr.decode("utf-8", errors="replace")
    return Done(done.returncode, out, err, done.stderr)


def write_suite(directory: Path, name: str, source: str) -> Path:
    """Write a suite file with the dedented source into directory and return its path."""
    path = directory / name
    path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    return path
