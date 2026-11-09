"""The command python -m budtestlibrary run: the suites of a folder or a file run in one process,
their neighbours imported by package name, the pattern, skipped names, and the summary and exit
code for passing, failing, unreadable, empty and missing paths."""

from pathlib import Path

from budtestlibrary import BudTestCase
from tests import support

PASSING = """
    from budtestlibrary import BudTestCase


    class {name}(BudTestCase):
        def bud_holds(self):
            self.assertEqual(1, 1, msg="one is one")
    """
FAILING = """
    from budtestlibrary import BudTestCase


    class {name}(BudTestCase):
        def bud_breaks(self):
            self.assertEqual(1, 2, msg="one is two")
    """
BASE = """
    from budtestlibrary import BudTestCase

    LIMIT = 5


    class LimitBase(BudTestCase):
        def bud_needs_a_subclass(self):
            self.assertEqual(LIMIT, 0, msg="a base class is not a suite of its own")
    """
HELPER = """
    LIMIT = 5
    """
USES_BASE = """
    from budtestlibrary import BudTestCase

    from suites.base import LIMIT


    class {name}(BudTestCase):
        def bud_reads_the_limit(self):
            self.assertEqual(LIMIT, 5, msg="the limit comes from suites.base")
    """
BROKEN = """
    import a_module_that_does_not_exist
    """


def project(name: str, files: dict) -> Path:
    """Write a project whose package suites/ holds the files, and return the project directory."""
    root = support.work_dir(name)
    package = root / "suites"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    for filename, source in files.items():
        support.write_suite(package, filename, source)
    return root


def run_command(root: Path, *args) -> support.Done:
    """Run python -m budtestlibrary run with the arguments in the project directory."""
    return support.python("-m", "budtestlibrary", "run", *args, cwd=root)


class RunCommand(BudTestCase):
    """The run command: which suites run, how the run is summarised, and its exit code."""

    def bud_runs_every_suite_of_a_folder(self):
        """Two passing suites in suites/: both run in one process and the run exits 0."""
        root = project(
            "run-folder",
            {
                "brakes.py": PASSING.format(name="BrakeTest"),
                "thermal.py": PASSING.format(name="ThermalTest"),
            },
        )
        done = run_command(root, "suites")
        support.check(self, done.code, 0, "run exits 0 when both suites pass", repr(done))
        support.check_in(
            self,
            "2 suite(s) ran in suites, 0 failed",
            done.out,
            "the summary counts two suites and no failure",
            f"the summary does not count two suites and no failure: {done!r}",
        )
        for name in ("BrakeTest", "ThermalTest"):
            support.check_in(
                self,
                f"STARTING TEST CASE EXECUTION: {name}",
                done.out + done.err,
                f"{name} runs",
                f"{name} did not run: {done!r}",
            )

    def bud_a_failing_suite_fails_the_run(self):
        """A failing suite beside a passing one: both run, the failing one is named, exit 1."""
        root = project(
            "run-failing",
            {
                "brakes.py": PASSING.format(name="BrakeTest"),
                "thermal.py": FAILING.format(name="ThermalTest"),
            },
        )
        done = run_command(root, "suites")
        support.check(self, done.code, 1, "run exits 1 when a suite fails", repr(done))
        support.check_in(
            self,
            "2 suite(s) ran in suites, 1 failed",
            done.out,
            "the summary counts two suites and one failure",
            f"the summary does not count two suites and one failure: {done!r}",
        )
        support.check_in(
            self,
            "FAILED suites.thermal.ThermalTest",
            done.out,
            "the failing suite is named",
            f"the failing suite is not named: {done!r}",
        )
        support.check_not_in(
            self,
            "FAILED suites.brakes.BrakeTest",
            done.out,
            "the passing suite is not named as failed",
            f"the passing suite is named as failed: {done!r}",
        )

    def bud_suites_import_their_neighbours_by_package_name(self):
        """A suite importing suites.base runs; --pattern leaves out base.py, whose base class
        fails when run on its own."""
        root = project(
            "run-neighbours",
            {"base.py": BASE, "test_limit.py": USES_BASE.format(name="LimitTest")},
        )
        done = run_command(root, "suites", "--pattern", "test_*.py")
        support.check(
            self, done.code, 0, "run exits 0 when the suite reads suites.base", repr(done)
        )
        support.check_in(
            self,
            "1 suite(s) ran in suites, 0 failed",
            done.out,
            "only the file matching test_*.py runs",
            f"not exactly the file matching test_*.py ran: {done!r}",
        )

    def bud_a_module_that_cannot_be_imported_fails_the_run(self):
        """A module failing to import is named with its error, the others still run, exit 1."""
        root = project(
            "run-unreadable",
            {"brakes.py": PASSING.format(name="BrakeTest"), "broken.py": BROKEN},
        )
        done = run_command(root, "suites")
        support.check(
            self, done.code, 1, "run exits 1 when a module cannot be imported", repr(done)
        )
        support.check_in(
            self,
            "NOT IMPORTED suites.broken",
            done.out,
            "the module that cannot be imported is named",
            f"the module that cannot be imported is not named: {done!r}",
        )
        support.check_in(
            self,
            "ModuleNotFoundError",
            done.out,
            "its import error is printed",
            f"its import error is not printed: {done!r}",
        )
        support.check_in(
            self,
            "1 suite(s) ran in suites, 0 failed",
            done.out,
            "the importable suite still runs",
            f"the importable suite did not run: {done!r}",
        )

    def bud_a_folder_without_suites_fails_the_run(self):
        """A folder holding no BudTestCase class runs nothing and exits 1."""
        root = project("run-empty", {"helper.py": HELPER})
        done = run_command(root, "suites")
        support.check(self, done.code, 1, "run exits 1 when no suite is found", repr(done))
        support.check_in(
            self,
            "no BudTestCase suite found in suites",
            done.out,
            "the run says no suite was found",
            f"the run does not say no suite was found: {done!r}",
        )

    def bud_a_missing_path_exits_2(self):
        """A path that does not exist is refused with exit 2."""
        root = project("run-missing", {})
        done = run_command(root, "nowhere")
        support.check(self, done.code, 2, "run exits 2 for a missing path", repr(done))
        support.check_in(
            self,
            "nowhere does not exist",
            done.err,
            "stderr says the path does not exist",
            f"stderr does not say the path does not exist: {done!r}",
        )

    def bud_names_starting_with_an_underscore_are_skipped(self):
        """A suite in _draft.py is not run."""
        root = project(
            "run-underscore",
            {
                "brakes.py": PASSING.format(name="BrakeTest"),
                "_draft.py": FAILING.format(name="DraftTest"),
            },
        )
        done = run_command(root, "suites")
        support.check(self, done.code, 0, "run exits 0 when only _draft.py fails", repr(done))
        support.check_in(
            self,
            "1 suite(s) ran in suites, 0 failed",
            done.out,
            "only brakes.py runs",
            f"not exactly brakes.py ran: {done!r}",
        )

    def bud_a_file_runs_alone(self):
        """A file path runs that file's suite and no other."""
        root = project(
            "run-file",
            {
                "brakes.py": PASSING.format(name="BrakeTest"),
                "thermal.py": FAILING.format(name="ThermalTest"),
            },
        )
        done = run_command(root, "suites/brakes.py")
        support.check(self, done.code, 0, "run exits 0 for the passing file", repr(done))
        support.check_in(
            self,
            "1 suite(s) ran in suites/brakes.py, 0 failed",
            done.out,
            "only brakes.py runs",
            f"not exactly brakes.py ran: {done!r}",
        )

    def bud_the_script_entry_imports_from_the_current_directory(self):
        """main() run without the current directory on sys.path, as the budtestlibrary script
        is, still imports the suites from it."""
        root = project("run-script", {"brakes.py": PASSING.format(name="BrakeTest")})
        done = support.python(
            "-I",
            "-c",
            "from budtestlibrary.__main__ import main; raise SystemExit(main(['run', 'suites']))",
            cwd=root,
        )
        support.check(self, done.code, 0, "the script entry runs the suite", repr(done))
        support.check_in(
            self,
            "1 suite(s) ran in suites, 0 failed",
            done.out,
            "the suite is imported from the current directory",
            f"the suite was not imported from the current directory: {done!r}",
        )
