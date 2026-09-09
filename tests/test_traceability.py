"""Checking what a suite claims about Bloom before it runs."""

import json
from textwrap import dedent

import pytest

from budtestlibrary.__main__ import main
from budtestlibrary.traceability import collect

TRACED = dedent(
    """
    from budtestlibrary import BloomMetaData, BudTestCase


    class {name}(BudTestCase):
        bloom_metadata = BloomMetaData("{project}", "{suffix}")

        def test_it(self):
            pass
    """
)

UNTRACED = dedent(
    """
    from budtestlibrary import BudTestCase


    class {name}(BudTestCase):
        def test_it(self):
            pass
    """
)


@pytest.fixture
def suite(tmp_path):
    def write(filename: str, source: str) -> None:
        (tmp_path / filename).write_text(source)

    return tmp_path, write


def test_collects_the_bloom_id_each_class_claims(suite):
    root, write = suite
    write("test_brakes.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))
    write("test_thermal.py", TRACED.format(name="ThermalTest", project="FLT", suffix="002"))

    report = collect(root)

    assert sorted(report.traced) == ["FLT-TC-001", "FLT-TC-002"]
    assert report.untraced == []
    assert report.ok


def test_finds_two_classes_claiming_one_test_case(suite):
    root, write = suite
    write("test_brakes.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))
    write("test_thermal.py", TRACED.format(name="ThermalTest", project="FLT", suffix="001"))

    report = collect(root)

    assert list(report.duplicates) == ["FLT-TC-001"]
    assert sorted(ref.name for ref in report.duplicates["FLT-TC-001"]) == [
        "BrakeTest",
        "ThermalTest",
    ]
    assert not report.ok


def test_lists_a_class_that_claims_nothing(suite):
    root, write = suite
    write("test_loose.py", UNTRACED.format(name="LooseTest"))

    report = collect(root)

    assert [ref.name for ref in report.untraced] == ["LooseTest"]
    assert report.ok


def test_a_module_that_will_not_import_is_reported_not_raised(suite):
    root, write = suite
    write("test_broken.py", "import a_module_that_is_not_installed\n")

    report = collect(root)

    assert len(report.unreadable) == 1
    assert "test_broken.py" in report.unreadable[0][0]
    assert not report.ok


def test_the_base_class_is_not_a_test_case(suite):
    root, write = suite
    write("test_nothing.py", "from budtestlibrary import BudTestCase\n")

    report = collect(root)

    assert report.traced == {}
    assert report.untraced == []


def test_a_class_is_counted_once_however_many_modules_import_it(suite):
    root, write = suite
    write("test_brakes.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))
    write("test_reexport.py", "from test_brakes import BrakeTest\n")

    report = collect(root)

    assert list(report.traced) == ["FLT-TC-001"]
    assert len(report.traced["FLT-TC-001"]) == 1


def test_a_single_file_can_be_checked(suite):
    root, write = suite
    write("test_brakes.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))

    report = collect(root / "test_brakes.py")

    assert list(report.traced) == ["FLT-TC-001"]


class TestTheCommand:
    def test_a_clean_suite_passes(self, suite, capsys):
        root, write = suite
        write("test_brakes.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))

        assert main(["check", str(root)]) == 0
        assert "FLT-TC-001" not in capsys.readouterr().out

    def test_a_duplicate_fails_and_names_both(self, suite, capsys):
        root, write = suite
        write("a.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))
        write("b.py", TRACED.format(name="ThermalTest", project="FLT", suffix="001"))

        assert main(["check", str(root)]) == 1
        out = capsys.readouterr().out
        assert "FLT-TC-001 is claimed by 2 test classes" in out
        assert "BrakeTest" in out and "ThermalTest" in out

    def test_strict_fails_on_a_class_that_claims_nothing(self, suite):
        root, write = suite
        write("test_loose.py", UNTRACED.format(name="LooseTest"))

        assert main(["check", str(root)]) == 0
        assert main(["check", str(root), "--strict"]) == 1

    def test_json_is_machine_readable(self, suite, capsys):
        root, write = suite
        write("a.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))
        write("b.py", TRACED.format(name="ThermalTest", project="FLT", suffix="001"))

        main(["check", str(root), "--json"])

        report = json.loads(capsys.readouterr().out)
        assert report["ok"] is False
        assert list(report["duplicates"]) == ["FLT-TC-001"]

    def test_list_prints_the_map(self, suite, capsys):
        root, write = suite
        write("a.py", TRACED.format(name="BrakeTest", project="FLT", suffix="001"))

        main(["check", str(root), "--list"])

        assert "FLT-TC-001" in capsys.readouterr().out

    def test_a_path_that_does_not_exist_is_refused(self, tmp_path, capsys):
        assert main(["check", str(tmp_path / "nowhere")]) == 2
        assert "does not exist" in capsys.readouterr().err
