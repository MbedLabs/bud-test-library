"""The examples shipped in budtestlibrary.examples: the package and its module list, imports, script runs, passing results, Bloom ids and the flashing example."""

import importlib
import inspect
from pathlib import Path

import support

import budtestlibrary.examples
from budtestlibrary import BudTestCase, parameterized

EXPECTED_EXAMPLE_MODULES = [
    "minimal_test",
    "bloom_metadata_test",
    "flash_event_example",
    "hil_test",
    "sil_test",
    "api_testing_example",
    "ui_testing_example",
    "cloud_e2e_example",
]
NON_TC_MODULES = {"flash_event_example"}
TC_MODULES = [m for m in EXPECTED_EXAMPLE_MODULES if m not in NON_TC_MODULES]
EXAMPLES_DIR = Path(budtestlibrary.examples.__file__).resolve().parent


def modules_on_disk() -> set[str]:
    """Return the module names of the .py files in the installed examples package, without __init__."""
    return {p.stem for p in EXAMPLES_DIR.glob("*.py") if p.name != "__init__.py"}


def case_class(module_name: str) -> type:
    """Return the BudTestCase subclass an example module defines."""
    module = importlib.import_module(f"budtestlibrary.examples.{module_name}")
    found = [
        obj
        for obj in vars(module).values()
        if inspect.isclass(obj)
        and issubclass(obj, BudTestCase)
        and obj.__module__ == module.__name__
    ]
    if len(found) != 1:
        raise RuntimeError(f"{module_name} defines {len(found)} BudTestCase classes")
    return found[0]


class BundledExamples(BudTestCase):
    """The examples bundled in budtestlibrary.examples."""

    def bud_examples_package_is_importable(self):
        """budtestlibrary.examples imports and has a module docstring."""
        support.check(
            self,
            bool(budtestlibrary.examples.__doc__),
            True,
            "budtestlibrary.examples imports and has a module docstring",
            "budtestlibrary.examples has no module docstring",
        )

    def bud_all_expected_modules_present(self):
        """Every expected example module is in the package."""
        support.check(
            self,
            sorted(set(EXPECTED_EXAMPLE_MODULES) - modules_on_disk()),
            [],
            "every expected example module is in budtestlibrary/examples",
            "some expected example modules are missing from budtestlibrary/examples",
        )

    def bud_no_orphan_example_files(self):
        """No example module is in the package without being in the expected list."""
        support.check(
            self,
            sorted(modules_on_disk() - set(EXPECTED_EXAMPLE_MODULES)),
            [],
            "budtestlibrary/examples holds no module outside the expected list",
            "budtestlibrary/examples holds modules that are not in the expected list",
        )

    @parameterized(EXPECTED_EXAMPLE_MODULES)
    def bud_example_imports(self, module_name):
        """The example module imports."""
        module = importlib.import_module(f"budtestlibrary.examples.{module_name}")
        support.check(
            self,
            module.__name__,
            f"budtestlibrary.examples.{module_name}",
            f"budtestlibrary.examples.{module_name} imports",
            f"importing budtestlibrary.examples.{module_name} gave another module",
        )

    @parameterized(EXPECTED_EXAMPLE_MODULES)
    def bud_example_runs_without_error(self, module_name):
        """Run as a script, the example exits 0 and its suite reports PASSED (the flashing example prints its results)."""
        done = support.python(EXAMPLES_DIR / f"{module_name}.py", timeout=60)
        support.check(
            self,
            done.code,
            0,
            f"the example {module_name}.py run as a script exits 0",
            f"the example {module_name}.py run as a script did not exit 0: {done.err[-500:]!r}",
        )
        if module_name in NON_TC_MODULES:
            support.check_in(
                self,
                "Success: True",
                done.out,
                f"{module_name}.py prints the successful flash as Success: True",
                f"{module_name}.py does not print Success: True for the successful flash",
            )
            support.check_in(
                self,
                "Recoverable: False",
                done.out,
                f"{module_name}.py prints the failed flash as Recoverable: False",
                f"{module_name}.py does not print Recoverable: False for the failed flash",
            )
        else:
            name = case_class(module_name).__name__
            summary = [line for line in done.err.splitlines() if "TEST CASE SUMMARY:" in line]
            support.check(
                self,
                len(summary),
                1,
                f"{module_name}.py prints exactly one TEST CASE SUMMARY line",
                f"{module_name}.py does not print exactly one TEST CASE SUMMARY line",
            )
            support.check_in(
                self,
                f"{name} - PASSED",
                summary[0],
                f"the summary of {module_name}.py says {name} - PASSED",
                f"the summary of {module_name}.py does not say {name} - PASSED",
            )

    @parameterized(TC_MODULES)
    def bud_every_example_passes(self, module_name):
        """Each example suite run in process returns True and has at least one step, every step passed."""
        returned, results = support.run(case_class(module_name)())
        support.check(
            self,
            returned,
            True,
            f"run() of the example {module_name} returns True",
            f"run() of the example {module_name} does not return True",
        )
        support.check(
            self,
            len(results) > 0,
            True,
            f"the example {module_name} has at least one step",
            f"the example {module_name} ran no step",
        )
        support.check(
            self,
            [r.passed for r in results],
            [True] * len(results),
            f"every step of the example {module_name} passes",
            f"some steps of the example {module_name} fail",
        )

    def bud_bloom_metadata_tc_id_present(self):
        """Every step of the Bloom metadata example carries tc_id PRJ-TC-001."""
        from budtestlibrary.examples.bloom_metadata_test import MotorControllerTest

        _, results = support.run(MotorControllerTest())
        support.check(
            self,
            [r.metadata.get("tc_id") for r in results],
            ["PRJ-TC-001"] * 2,
            "both steps of MotorControllerTest carry tc_id PRJ-TC-001",
            "the steps of MotorControllerTest do not both carry tc_id PRJ-TC-001",
        )

    def bud_flash_event_example(self):
        """The ESP32 example reports its info, flashes a .bin at the default address and refuses another file for good."""
        from budtestlibrary.examples.flash_event_example import ESP32FlashEvent

        event = ESP32FlashEvent()
        support.check(
            self,
            event.get_info(),
            {
                "project_name": "ESP32-SensorHub",
                "firmware_version": "2.1.0",
                "release": "production",
            },
            "ESP32FlashEvent.get_info() names project ESP32-SensorHub, firmware 2.1.0, release production",
            "ESP32FlashEvent.get_info() differs from project ESP32-SensorHub, firmware 2.1.0, release production",
        )
        success = event.execute("fw.bin")
        support.check(
            self,
            success.is_success(),
            True,
            "flashing fw.bin succeeds",
            "flashing fw.bin failed",
        )
        support.check(
            self,
            success.message,
            "Flashed fw.bin to ESP32 at 0x10000",
            "the success message names the default address 0x10000",
            "the success message does not read Flashed fw.bin to ESP32 at 0x10000",
        )
        support.check(
            self,
            event.get_duration() is not None,
            True,
            "the flash event measures its duration",
            "the flash event did not measure its duration",
        )
        failure = event.execute("invalid_file.txt")
        support.check(
            self,
            failure.is_success(),
            False,
            "flashing invalid_file.txt fails",
            "flashing invalid_file.txt succeeded",
        )
        support.check(
            self,
            failure.recoverable,
            False,
            "the failed flash of invalid_file.txt is not recoverable",
            "the failed flash of invalid_file.txt is marked recoverable",
        )
