"""Bloom traceability: collect() on suite files and the command python -m budtestlibrary check with its options and exit codes."""

import json
import sys
import textwrap
from pathlib import Path

from budtestlibrary import BudTestCase
from budtestlibrary.traceability import collect
from tests import support

TRACED = textwrap.dedent("""
    from budtestlibrary import BloomMetaData, BudTestCase


    class {name}(BudTestCase):
        bloom_metadata = BloomMetaData("{project}", "{suffix}")

        def bud_it(self):
            pass
    """)
UNTRACED = textwrap.dedent("""
    from budtestlibrary import BudTestCase


    class {name}(BudTestCase):
        def bud_it(self):
            pass
    """)


def suite_dir(name: str, files: dict):
    """Write the files into a new directory and return it."""
    root = support.work_dir(name)
    for filename, source in files.items():
        (root / filename).write_text(source, encoding="utf-8")
    return root


def traced(name: str, suffix: str) -> str:
    """Return the source of a suite class claiming PRJ-TC-<suffix>."""
    return TRACED.format(name=name, project="PRJ", suffix=suffix)


def check_command(*args) -> support.Done:
    """Run python -m budtestlibrary check with the arguments."""
    return support.python("-m", "budtestlibrary", "check", *args)


class Traceability(BudTestCase):
    """The traceability check: the Bloom test case each class claims, duplicates, unclaimed classes, and the command's output and exit code."""

    def bud_collects_the_bloom_id_each_class_claims(self):
        """Two files claiming PRJ-TC-001 and PRJ-TC-002: both traced, nothing untraced, ok."""
        root = suite_dir(
            "collect",
            {
                "test_brakes.py": traced("BrakeTest", "001"),
                "test_thermal.py": traced("ThermalTest", "002"),
            },
        )
        report = collect(root)
        support.check(
            self,
            sorted(report.traced),
            ["PRJ-TC-001", "PRJ-TC-002"],
            "collect() traces PRJ-TC-001 to test_brakes.py and PRJ-TC-002 to test_thermal.py",
            "collect() did not trace exactly PRJ-TC-001 and PRJ-TC-002 from test_brakes.py and test_thermal.py",
        )
        support.check(
            self,
            report.untraced,
            [],
            "collect() lists no untraced class when every class carries Bloom metadata",
            "collect() listed an untraced class although every class carries Bloom metadata",
        )
        support.check(
            self,
            report.ok,
            True,
            "collect() reports ok for two classes claiming two different Bloom ids",
            "collect() reported not ok for two classes claiming two different Bloom ids",
        )

    def bud_finds_two_classes_claiming_one_test_case(self):
        """Two classes claiming PRJ-TC-001 are a duplicate naming both; not ok."""
        root = suite_dir(
            "duplicate",
            {
                "test_brakes.py": traced("BrakeTest", "001"),
                "test_thermal.py": traced("ThermalTest", "001"),
            },
        )
        report = collect(root)
        support.check(
            self,
            list(report.duplicates),
            ["PRJ-TC-001"],
            "collect() reports PRJ-TC-001 as duplicated when BrakeTest and ThermalTest both claim it",
            "collect() did not report PRJ-TC-001 as the only duplicate although BrakeTest and ThermalTest both claim it",
        )
        support.check(
            self,
            sorted(ref.name for ref in report.duplicates["PRJ-TC-001"]),
            ["BrakeTest", "ThermalTest"],
            "the PRJ-TC-001 duplicate names both claiming classes, BrakeTest and ThermalTest",
            "the PRJ-TC-001 duplicate does not name exactly BrakeTest and ThermalTest",
        )
        support.check(
            self,
            report.ok,
            False,
            "collect() reports not ok when one Bloom id is claimed by two classes",
            "collect() reported ok although one Bloom id is claimed by two classes",
        )

    def bud_lists_a_class_that_claims_nothing(self):
        """A class without metadata is untraced and the report stays ok."""
        report = collect(
            suite_dir("untraced", {"test_loose.py": UNTRACED.format(name="LooseTest")})
        )
        support.check(
            self,
            [ref.name for ref in report.untraced],
            ["LooseTest"],
            "collect() lists LooseTest, which has no Bloom metadata, as untraced",
            "collect() did not list LooseTest, which has no Bloom metadata, as the only untraced class",
        )
        support.check(
            self,
            report.ok,
            True,
            "an untraced class alone does not make collect() report not ok",
            "collect() reported not ok for a suite whose only problem is an untraced class",
        )

    def bud_a_module_that_will_not_import_is_reported_not_raised(self):
        """A module importing a missing package is one unreadable entry naming the file; not ok."""
        report = collect(
            suite_dir("broken", {"test_broken.py": "import a_module_that_is_not_installed\n"})
        )
        support.check(
            self,
            len(report.unreadable),
            1,
            "collect() records test_broken.py, which imports a missing package, as one unreadable module",
            "collect() did not record exactly one unreadable module for test_broken.py, which imports a missing package",
        )
        support.check(
            self,
            Path(report.unreadable[0][0]).name,
            "test_broken.py",
            "the unreadable entry names the module that failed to import, test_broken.py",
            "the unreadable entry names another file than test_broken.py, the module that failed to import",
        )
        support.check(
            self,
            report.ok,
            False,
            "collect() reports not ok when a suite module cannot be imported",
            "collect() reported ok although a suite module cannot be imported",
        )

    def bud_the_base_class_is_not_a_test_case(self):
        """A module that only imports BudTestCase yields nothing."""
        report = collect(
            suite_dir("base-only", {"test_nothing.py": "from budtestlibrary import BudTestCase\n"})
        )
        support.check(
            self,
            (report.traced, report.untraced),
            ({}, []),
            "a module that only imports BudTestCase yields no traced and no untraced class",
            "a module that only imports BudTestCase produced a traced or untraced class",
        )

    def bud_a_class_is_counted_once_however_many_modules_import_it(self):
        """A second module that imports the first module's class does not count it again and is readable."""
        root = suite_dir(
            "reexport",
            {
                "demo_brakes.py": traced("BrakeTest", "001"),
                "demo_reexport.py": "from demo_brakes import BrakeTest\n",
            },
        )
        sys.path.insert(0, str(root))
        try:
            report = collect(root)
        finally:
            sys.path.remove(str(root))
            sys.modules.pop("demo_brakes", None)
        support.check(
            self,
            report.unreadable,
            [],
            "collect() imports demo_brakes.py and demo_reexport.py without an unreadable entry",
            "collect() recorded an unreadable entry for demo_brakes.py or demo_reexport.py",
        )
        support.check(
            self,
            list(report.traced),
            ["PRJ-TC-001"],
            "PRJ-TC-001 is the only Bloom id traced when a second module re-exports BrakeTest",
            "a second module re-exporting BrakeTest changed the traced Bloom ids from only PRJ-TC-001",
        )
        support.check(
            self,
            len(report.traced["PRJ-TC-001"]),
            1,
            "BrakeTest is counted once for PRJ-TC-001 although two modules expose it",
            "BrakeTest is counted more than once for PRJ-TC-001 because two modules expose it",
        )

    def bud_a_single_file_can_be_checked(self):
        """collect() on one file reads that file."""
        root = suite_dir("single", {"test_brakes.py": traced("BrakeTest", "001")})
        support.check(
            self,
            list(collect(root / "test_brakes.py").traced),
            ["PRJ-TC-001"],
            "collect() on the single file test_brakes.py traces PRJ-TC-001",
            "collect() on the single file test_brakes.py did not trace exactly PRJ-TC-001",
        )

    def bud_a_clean_suite_passes(self):
        """check on a clean suite exits 0, does not print the id and ends with the summary."""
        root = suite_dir("clean", {"test_brakes.py": traced("BrakeTest", "001")})
        done = check_command(root)
        support.check(
            self,
            done.code,
            0,
            "budtestlibrary check exits 0 on a suite where one class claims one Bloom id",
            "budtestlibrary check did not exit 0 on a suite where one class claims one Bloom id",
        )
        support.check_not_in(
            self,
            "PRJ-TC-001",
            done.out,
            "budtestlibrary check does not print PRJ-TC-001 when --list is not given",
            "budtestlibrary check printed PRJ-TC-001 although --list was not given",
        )
        support.check(
            self,
            done.out.strip().splitlines()[-1],
            "1 test class(es): 1 claim 1 Bloom test case(s), 0 claim none, 0 id(s) duplicated.",
            "budtestlibrary check ends with the summary of 1 class, 1 claim, 0 untraced and 0 duplicated",
            "budtestlibrary check did not end with the summary of 1 class, 1 claim, 0 untraced and 0 duplicated",
        )

    def bud_a_duplicate_fails_and_names_both(self):
        """check on a duplicate exits 1 and names the id and both classes."""
        root = suite_dir(
            "cli-duplicate",
            {"a.py": traced("BrakeTest", "001"), "b.py": traced("ThermalTest", "001")},
        )
        done = check_command(root)
        support.check(
            self,
            done.code,
            1,
            "budtestlibrary check exits 1 when PRJ-TC-001 is claimed by BrakeTest and ThermalTest",
            "budtestlibrary check did not exit 1 although PRJ-TC-001 is claimed by BrakeTest and ThermalTest",
        )
        support.check_in(
            self,
            "✗ PRJ-TC-001 is claimed by 2 test classes:",
            done.out,
            "budtestlibrary check prints that PRJ-TC-001 is claimed by 2 test classes",
            "budtestlibrary check did not print that PRJ-TC-001 is claimed by 2 test classes",
        )
        support.check_in(
            self,
            f"    {root / 'a.py'}::BrakeTest",
            done.out,
            "the duplicate report lists a.py::BrakeTest as a claimant",
            "the duplicate report does not list a.py::BrakeTest as a claimant",
        )
        support.check_in(
            self,
            f"    {root / 'b.py'}::ThermalTest",
            done.out,
            "the duplicate report lists b.py::ThermalTest as a claimant",
            "the duplicate report does not list b.py::ThermalTest as a claimant",
        )

    def bud_strict_fails_on_a_class_that_claims_nothing(self):
        """An untraced class: exit 0 without --strict and 1 with it."""
        root = suite_dir("strict", {"test_loose.py": UNTRACED.format(name="LooseTest")})
        support.check(
            self,
            check_command(root).code,
            0,
            "budtestlibrary check exits 0 on an untraced class when --strict is not given",
            "budtestlibrary check did not exit 0 on an untraced class without --strict",
        )
        support.check(
            self,
            check_command(root, "--strict").code,
            1,
            "budtestlibrary check --strict exits 1 on a suite holding an untraced class",
            "budtestlibrary check --strict did not exit 1 on a suite holding an untraced class",
        )

    def bud_json_is_machine_readable(self):
        """--json prints a JSON report with ok false and the duplicate, and exits 1."""
        root = suite_dir(
            "json", {"a.py": traced("BrakeTest", "001"), "b.py": traced("ThermalTest", "001")}
        )
        done = check_command(root, "--json")
        report = json.loads(done.out)
        support.check(
            self,
            report["ok"],
            False,
            "budtestlibrary check --json reports ok false for a duplicated Bloom id",
            "budtestlibrary check --json did not report ok false for a duplicated Bloom id",
        )
        support.check(
            self,
            list(report["duplicates"]),
            ["PRJ-TC-001"],
            "budtestlibrary check --json lists PRJ-TC-001 under duplicates",
            "budtestlibrary check --json does not list exactly PRJ-TC-001 under duplicates",
        )
        support.check(
            self,
            done.code,
            1,
            "budtestlibrary check --json exits 1 for a duplicated Bloom id",
            "budtestlibrary check --json did not exit 1 for a duplicated Bloom id",
        )

    def bud_list_prints_the_map(self):
        """--list prints the heading and one line per id with the class location."""
        root = suite_dir("list", {"a.py": traced("BrakeTest", "001")})
        done = check_command(root, "--list")
        support.check_in(
            self,
            "Bloom test cases this suite covers:",
            done.out,
            "budtestlibrary check --list prints the heading of the Bloom id map",
            "budtestlibrary check --list did not print the heading of the Bloom id map",
        )
        support.check_in(
            self,
            f"  PRJ-TC-001  {root / 'a.py'}::BrakeTest",
            done.out,
            "budtestlibrary check --list maps PRJ-TC-001 to a.py::BrakeTest",
            "budtestlibrary check --list does not map PRJ-TC-001 to a.py::BrakeTest",
        )

    def bud_a_path_that_does_not_exist_is_refused(self):
        """A path that does not exist exits 2 and says so on stderr."""
        missing = support.work_dir("nowhere") / "nowhere"
        done = check_command(missing)
        support.check(
            self,
            done.code,
            2,
            "budtestlibrary check exits 2 when the given path does not exist",
            "budtestlibrary check did not exit 2 for a path that does not exist",
        )
        support.check_in(
            self,
            f"{missing} does not exist",
            done.err,
            "budtestlibrary check names the missing path on stderr",
            "budtestlibrary check did not name the missing path on stderr",
        )

    def bud_an_unreadable_module_fails_the_command(self):
        """A suite holding a module that fails to import exits 1 and names the file."""
        root = suite_dir(
            "cli-broken", {"test_broken.py": "import a_module_that_is_not_installed\n"}
        )
        done = check_command(root)
        support.check(
            self,
            done.code,
            1,
            "budtestlibrary check exits 1 when a suite module cannot be imported",
            "budtestlibrary check did not exit 1 although a suite module cannot be imported",
        )
        support.check_in(
            self,
            f"✗ {root / 'test_broken.py'} could not be imported",
            done.out,
            "budtestlibrary check names test_broken.py as the module that could not be imported",
            "budtestlibrary check did not name test_broken.py as the module that could not be imported",
        )
