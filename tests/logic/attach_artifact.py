"""attach_artifact(): the artifacts in a step result's metadata, relative paths and names, per-step lists, missing files and directories, and calls from setUp, tearDown and setUpClass."""

import logging
import os

from budtestlibrary import BudTestCase
from tests import support


class AttachArtifact(BudTestCase):
    """attach_artifact() and the artifacts each step result records."""

    def bud_existing_file_is_recorded_with_absolute_path_and_file_name(self):
        """An existing file is listed with its absolute path and file name, also in to_dict()."""
        log_file = support.work_dir("artifact") / "capture.log"
        log_file.write_text("trace")

        class ArtifactTest(BudTestCase):
            def bud_capture(self):
                self.attach_artifact(log_file)

        _, results = support.run(ArtifactTest())
        result = results[0]
        want = [{"path": str(log_file), "name": "capture.log"}]
        support.check(
            self,
            result.passed,
            True,
            "the step that attaches the existing capture.log passes",
            "the step that attaches the existing capture.log failed",
        )
        support.check(
            self,
            result.metadata.get("artifacts"),
            want,
            "the step's metadata lists capture.log with its absolute path and file name",
            "the step's metadata does not list capture.log with its absolute path and file name",
        )
        support.check(
            self,
            result.to_dict()["metadata"].get("artifacts"),
            want,
            "to_dict() carries the same artifacts entry for capture.log",
            "to_dict() does not carry the artifacts entry for capture.log",
        )

    def bud_explicit_name_and_relative_path(self):
        """A relative path is resolved against the working directory and the given name is kept."""
        directory = support.work_dir("relative")
        (directory / "out.bin").write_bytes(b"\x00")

        class ArtifactTest(BudTestCase):
            def bud_capture(self):
                self.attach_artifact("out.bin", name="firmware dump")

        saved = os.getcwd()
        os.chdir(directory)
        try:
            cwd = os.getcwd()
            _, results = support.run(ArtifactTest())
        finally:
            os.chdir(saved)
        want = [{"path": os.path.join(cwd, "out.bin"), "name": "firmware dump"}]
        support.check(
            self,
            results[0].metadata.get("artifacts"),
            want,
            "a relative path is listed with its absolute path in the working directory and the given name",
            "the relative path is not listed with its absolute path and the given name",
        )

    def bud_steps_without_attachments_have_no_artifacts_key(self):
        """A step that attaches nothing has no artifacts key."""

        class PlainTest(BudTestCase):
            def bud_plain(self):
                self.assertTrue(support.HOLDS)

        _, results = support.run(PlainTest())
        support.check_not_in(
            self,
            "artifacts",
            list(results[0].metadata),
            "a step that attaches nothing has no artifacts key in its metadata",
            "a step that attaches nothing has an artifacts key in its metadata",
        )

    def bud_artifacts_belong_to_the_step_that_attached_them(self):
        """Each step lists only its own files."""
        directory = support.work_dir("two-steps")
        first_file = directory / "first.log"
        second_file = directory / "second.log"
        first_file.write_text("1")
        second_file.write_text("2")

        class TwoSteps(BudTestCase):
            def bud_first(self):
                self.attach_artifact(first_file)

            def bud_middle(self):
                pass

            def bud_second(self):
                self.attach_artifact(second_file)

        _, results = support.run(TwoSteps())
        support.check(
            self,
            len(results),
            3,
            "the case runs three steps",
            "the case did not run exactly three steps",
        )
        first, middle, second = results
        support.check(
            self,
            [a["name"] for a in first.metadata.get("artifacts", [])],
            ["first.log"],
            "the first step lists only its own file first.log",
            "the first step does not list only first.log",
        )
        support.check_not_in(
            self,
            "artifacts",
            list(middle.metadata),
            "the middle step, which attaches nothing, has no artifacts key",
            "the middle step, which attaches nothing, has an artifacts key",
        )
        support.check(
            self,
            [a["name"] for a in second.metadata.get("artifacts", [])],
            ["second.log"],
            "the third step lists only its own file second.log",
            "the third step does not list only second.log",
        )

    def bud_missing_file_records_a_failed_entry_and_stops_the_step(self):
        """A missing file records a failed AttachArtifact entry with the path and stops the step."""
        missing = support.work_dir("missing") / "nope.log"

        class MissingTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.reached = False

            def bud_missing(self):
                self.attach_artifact(missing)
                self.reached = True

        case = MissingTest()
        _, results = support.run(case)
        result = results[0]
        support.check(
            self,
            case.reached,
            False,
            "attaching the missing nope.log stops the step before its next line",
            "the step went on past attaching the missing nope.log",
        )
        support.check(
            self,
            result.passed,
            False,
            "the step attaching the missing nope.log is reported as failed",
            "the step attaching the missing nope.log is reported as passed",
        )
        support.check(
            self,
            len(result.assertions),
            1,
            "attaching the missing nope.log records exactly one entry",
            "attaching the missing nope.log did not record exactly one entry",
        )
        entry = result.assertions[0]
        support.check(
            self,
            entry.assertion_type,
            "AttachArtifact",
            "the entry for the missing file is an AttachArtifact entry",
            "the entry for the missing file is of another type than AttachArtifact",
        )
        support.check(
            self,
            entry.passed,
            False,
            "the AttachArtifact entry for the missing file is failed",
            "the AttachArtifact entry for the missing file is passed",
        )
        support.check(
            self,
            entry.actual,
            str(missing),
            "the entry's actual value is the missing path",
            "the entry's actual value is not the missing path",
        )
        support.check(
            self,
            entry.message,
            f"Artifact file not found: {missing}",
            "the entry's message says Artifact file not found with the path",
            "the entry's message is not Artifact file not found with the path",
        )
        support.check_in(
            self,
            "Artifact file not found",
            result.error_message,
            "the step's error message says Artifact file not found",
            "the step's error message does not say Artifact file not found",
        )
        support.check_not_in(
            self,
            "artifacts",
            list(result.metadata),
            "the step with the missing file lists no artifacts",
            "the step with the missing file still lists artifacts",
        )

    def bud_directory_is_not_accepted(self):
        """A directory fails the step with an AttachArtifact entry."""
        directory = support.work_dir("directory")

        class DirectoryTest(BudTestCase):
            def bud_dir(self):
                self.attach_artifact(directory)

        _, results = support.run(DirectoryTest())
        support.check(
            self,
            results[0].passed,
            False,
            "attaching a directory fails the step",
            "attaching a directory did not fail the step",
        )
        support.check(
            self,
            results[0].assertions[0].assertion_type,
            "AttachArtifact",
            "attaching a directory records an AttachArtifact entry",
            "attaching a directory recorded another entry type than AttachArtifact",
        )
        support.check(
            self,
            results[0].assertions[0].passed,
            False,
            "the AttachArtifact entry for the directory is failed",
            "the AttachArtifact entry for the directory is passed",
        )

    def bud_attachment_in_teardown_is_kept_on_the_step(self):
        """A file attached in tearDown is listed on the step."""
        log_file = support.work_dir("teardown") / "teardown.log"
        log_file.write_text("x")

        class TearDownTest(BudTestCase):
            def tearDown(self):
                self.attach_artifact(log_file)

            def bud_step(self):
                pass

        _, results = support.run(TearDownTest())
        support.check(
            self,
            [a["name"] for a in results[0].metadata.get("artifacts", [])],
            ["teardown.log"],
            "teardown.log attached in tearDown is listed on the step",
            "teardown.log attached in tearDown is not listed on the step",
        )

    def bud_missing_file_in_setup_is_a_setup_failure(self):
        """A missing file in setUp fails the step as a setup failure with no entry on the step."""
        missing = support.work_dir("setup-missing") / "setup.log"

        class SetUpMissing(BudTestCase):
            def setUp(self):
                self.attach_artifact(missing)

            def bud_step(self):
                pass

        _, results = support.run(SetUpMissing())
        result = results[0]
        support.check(
            self,
            result.passed,
            False,
            "a missing file in setUp fails the step",
            "a missing file in setUp did not fail the step",
        )
        support.check(
            self,
            result.error_message[: len("setUp failed: [AttachArtifact]")],
            "setUp failed: [AttachArtifact]",
            "the step error says setUp failed: [AttachArtifact]",
            "the step error does not start with setUp failed: [AttachArtifact]",
        )
        support.check(
            self,
            result.assertions,
            [],
            "a setup failure leaves no entry on the step",
            "a setup failure left entries on the step",
        )

    def bud_missing_file_in_teardown_is_logged_only(self):
        """A missing file in tearDown leaves the step passed, without artifacts, and logs a cleanup failure."""
        missing = support.work_dir("teardown-missing") / "teardown.log"

        class TearDownMissing(BudTestCase):
            def tearDown(self):
                self.attach_artifact(missing)

            def bud_step(self):
                self.assertTrue(support.HOLDS)

        _, results, console = support.run_capturing(TearDownMissing(), logging.INFO)
        result = results[0]
        support.check(
            self,
            result.passed,
            True,
            "a missing file in tearDown leaves the step passed",
            "a missing file in tearDown failed the step",
        )
        support.check(
            self,
            result.error_message,
            None,
            "a missing file in tearDown gives the step no error message",
            "a missing file in tearDown gave the step an error message",
        )
        support.check_not_in(
            self,
            "artifacts",
            list(result.metadata),
            "a missing file in tearDown adds no artifacts to the step",
            "a missing file in tearDown added artifacts to the step",
        )
        support.check_in(
            self,
            "CLEANUP FAILURE DURING tearDown: [AttachArtifact]",
            console,
            "the missing file in tearDown is logged as a cleanup failure",
            "the missing file in tearDown is not logged as a cleanup failure",
        )

    def bud_attachment_in_setupclass_is_not_recorded(self):
        """A file attached in setUpClass belongs to no step: the first step passes without artifacts."""
        log_file = support.work_dir("class-level") / "class.log"
        log_file.write_text("x")

        class ClassLevel(BudTestCase):
            def setUpClass(self):
                self.attach_artifact(log_file)

            def bud_step(self):
                pass

        _, results = support.run(ClassLevel())
        support.check(
            self,
            results[0].passed,
            True,
            "the first step passes although setUpClass attached a file",
            "the first step failed after setUpClass attached a file",
        )
        support.check_not_in(
            self,
            "artifacts",
            list(results[0].metadata),
            "a file attached in setUpClass is listed on no step",
            "a file attached in setUpClass is listed on the first step",
        )
