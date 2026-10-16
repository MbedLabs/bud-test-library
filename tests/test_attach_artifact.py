"""Tests for attach_artifact() and the artifacts in step result metadata."""

import logging
import os

from budtestlibrary import BudTestCase


def _run(tc):
    """Run a test case instance quietly and return it."""
    tc.set_loglevel(logging.CRITICAL)
    tc.run()
    return tc


class TestAttachArtifact:
    def test_existing_file_is_recorded_with_absolute_path_and_file_name(self, tmp_path):
        log_file = tmp_path / "capture.log"
        log_file.write_text("trace")

        class ArtifactTest(BudTestCase):
            def bud_capture(self):
                self.attach_artifact(log_file)

        result = _run(ArtifactTest()).get_results()[0]
        assert result.passed is True
        assert result.metadata["artifacts"] == [{"path": str(log_file), "name": "capture.log"}]
        assert result.to_dict()["metadata"]["artifacts"] == result.metadata["artifacts"]

    def test_explicit_name_and_relative_path(self, tmp_path, monkeypatch):
        (tmp_path / "out.bin").write_bytes(b"\x00")
        monkeypatch.chdir(tmp_path)

        class ArtifactTest(BudTestCase):
            def bud_capture(self):
                self.attach_artifact("out.bin", name="firmware dump")

        result = _run(ArtifactTest()).get_results()[0]
        assert result.metadata["artifacts"] == [
            {"path": os.path.join(os.getcwd(), "out.bin"), "name": "firmware dump"}
        ]

    def test_steps_without_attachments_have_no_artifacts_key(self):
        class PlainTest(BudTestCase):
            def bud_plain(self):
                self.assertTrue(True)

        result = _run(PlainTest()).get_results()[0]
        assert "artifacts" not in result.metadata

    def test_artifacts_belong_to_the_step_that_attached_them(self, tmp_path):
        first_file = tmp_path / "first.log"
        second_file = tmp_path / "second.log"
        first_file.write_text("1")
        second_file.write_text("2")

        class TwoSteps(BudTestCase):
            def bud_first(self):
                self.attach_artifact(first_file)

            def bud_middle(self):
                pass

            def bud_second(self):
                self.attach_artifact(second_file)

        first, middle, second = _run(TwoSteps()).get_results()
        assert [a["name"] for a in first.metadata["artifacts"]] == ["first.log"]
        assert "artifacts" not in middle.metadata
        assert [a["name"] for a in second.metadata["artifacts"]] == ["second.log"]

    def test_missing_file_records_a_failed_entry_and_stops_the_step(self, tmp_path):
        missing = tmp_path / "nope.log"

        class MissingTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.reached = False

            def bud_missing(self):
                self.attach_artifact(missing)
                self.reached = True

        tc = _run(MissingTest())
        result = tc.get_results()[0]
        assert tc.reached is False
        assert result.passed is False
        entry = result.assertions[0]
        assert entry.assertion_type == "AttachArtifact"
        assert entry.passed is False
        assert entry.actual == str(missing)
        assert "Artifact file not found" in result.error_message
        assert "artifacts" not in result.metadata

    def test_directory_is_not_accepted(self, tmp_path):
        class DirectoryTest(BudTestCase):
            def bud_dir(self):
                self.attach_artifact(tmp_path)

        result = _run(DirectoryTest()).get_results()[0]
        assert result.passed is False
        assert result.assertions[0].assertion_type == "AttachArtifact"

    def test_attachment_in_teardown_is_kept_on_the_step(self, tmp_path):
        log_file = tmp_path / "teardown.log"
        log_file.write_text("x")

        class TearDownTest(BudTestCase):
            def tearDown(self):
                self.attach_artifact(log_file)

            def bud_step(self):
                pass

        result = _run(TearDownTest()).get_results()[0]
        assert [a["name"] for a in result.metadata["artifacts"]] == ["teardown.log"]

    def test_missing_file_in_setup_is_a_setup_failure(self):
        class SetUpMissing(BudTestCase):
            def setUp(self):
                self.attach_artifact("/nonexistent/setup.log")

            def bud_step(self):
                pass

        result = _run(SetUpMissing()).get_results()[0]
        assert result.passed is False
        assert result.error_message.startswith("setUp failed: [AttachArtifact]")
        assert result.assertions == []

    def test_missing_file_in_teardown_is_logged_only(self):
        class TearDownMissing(BudTestCase):
            def tearDown(self):
                self.attach_artifact("/nonexistent/teardown.log")

            def bud_step(self):
                self.assertTrue(True)

        result = _run(TearDownMissing()).get_results()[0]
        assert result.passed is True
        assert result.error_message is None
        assert "artifacts" not in result.metadata

    def test_attachment_in_setupclass_is_not_recorded(self, tmp_path):
        log_file = tmp_path / "class.log"
        log_file.write_text("x")

        class ClassLevel(BudTestCase):
            def setUpClass(self):
                self.attach_artifact(log_file)

            def bud_step(self):
                pass

        result = _run(ClassLevel()).get_results()[0]
        assert result.passed is True
        assert "artifacts" not in result.metadata
