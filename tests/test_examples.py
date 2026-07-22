"""Verify that all bundled example modules import and run successfully."""

import logging
import subprocess
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "budtestlibrary" / "examples"

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

# Modules that don't contain a BudTestCase subclass (e.g. FlashEvent-only examples)
NON_TC_MODULES = {"flash_event_example"}


def _python_module_name(path: Path) -> str:
    return path.stem


def example_modules():
    """Return every .py module in the examples directory (excluding __init__)."""
    if not EXAMPLES_DIR.is_dir():
        return []
    return [
        _python_module_name(f)
        for f in sorted(EXAMPLES_DIR.glob("*.py"))
        if f.name != "__init__.py"
    ]


def tc_example_modules():
    """Return example modules that contain a BudTestCase subclass."""
    return [m for m in example_modules() if m not in NON_TC_MODULES]


class TestExamplesPackaging:
    """Ensure the examples sub-package is complete and importable."""

    def test_examples_package_is_importable(self):
        import budtestlibrary.examples

        assert budtestlibrary.examples.__doc__ is not None

    def test_all_expected_modules_present(self):
        actual = set(example_modules())
        missing = set(EXPECTED_EXAMPLE_MODULES) - actual
        assert not missing, f"Missing example modules: {missing}"

    def test_no_orphan_example_files(self):
        actual = set(example_modules())
        extra = actual - set(EXPECTED_EXAMPLE_MODULES)
        assert not extra, (
            f"Untracked example modules found — add them to "
            f"EXPECTED_EXAMPLE_MODULES in this test: {extra}"
        )


class TestExampleImports:
    """Every example module must be importable (top-level import)."""

    @pytest.mark.parametrize("module_name", example_modules())
    def test_example_imports(self, module_name: str):
        mod = __import__(f"budtestlibrary.examples.{module_name}", fromlist=[module_name])
        assert mod is not None


class TestExampleRuns:
    """Every example module must execute as a script without errors."""

    @pytest.mark.parametrize("module_name", example_modules())
    def test_example_runs_without_error(self, module_name: str):
        script_path = EXAMPLES_DIR / f"{module_name}.py"
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Example {module_name} exited with code {result.returncode}\n"
            f"STDERR:\n{result.stderr}\n"
            f"STDOUT:\n{result.stdout}"
        )


class TestExampleResults:
    """Verify the result structure of each example when exercised programmatically."""

    def _import_and_get_class(self, module_name: str):
        mod = __import__(f"budtestlibrary.examples.{module_name}", fromlist=[module_name])
        test_classes = [
            v
            for v in mod.__dict__.values()
            if isinstance(v, type) and v.__name__.endswith("Test") and not v.__name__.startswith("Test")
        ]
        return test_classes[0] if test_classes else None

    @pytest.mark.parametrize("module_name", tc_example_modules())
    def test_every_example_passes(self, module_name: str):
        cls = self._import_and_get_class(module_name)
        assert cls is not None, f"No BudTestCase subclass found in {module_name}"
        tc = cls()
        tc.set_loglevel(logging.CRITICAL)
        passed = tc.run()
        assert passed, f"Example {module_name}.{cls.__name__}() did not pass"

    @pytest.mark.parametrize("module_name", tc_example_modules())
    def test_every_example_produces_results(self, module_name: str):
        cls = self._import_and_get_class(module_name)
        assert cls is not None, f"No BudTestCase subclass found in {module_name}"
        tc = cls()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        results = tc.get_results()
        assert len(results) > 0, f"Example {module_name} produced no results"
        for r in results:
            assert r.method_name.startswith("bud_"), (
                f"Non-test method {r.method_name!r} was discovered in {module_name}"
            )

    def test_bloom_metadata_tc_id_present(self):
        from budtestlibrary.examples.bloom_metadata_test import MotorControllerTest

        tc = MotorControllerTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        results = tc.get_results()
        for r in results:
            assert r.metadata.get("tc_id") == "MCU-TC-001", (
                f"Missing or wrong tc_id in {r.method_name}"
            )

    def test_flash_event_example(self):
        """Run the flash_event_example and verify it handles success and failure paths."""
        from budtestlibrary.examples.flash_event_example import ESP32FlashEvent

        event = ESP32FlashEvent()
        info = event.get_info()
        assert info["project_name"] == "ESP32-SensorHub"
        assert info["firmware_version"] == "2.1.0"
        assert info["release"] == "production"

        success = event.execute("fw.bin")
        assert success.is_success()
        assert event.get_duration() is not None

        failure = event.execute("invalid_file.txt")
        assert not failure.is_success()
        assert hasattr(failure, "recoverable")
        assert not failure.recoverable
