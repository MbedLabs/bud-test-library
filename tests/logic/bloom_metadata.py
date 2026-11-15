"""BloomMetaData: the full test case id, URLs, to_dict(), the optional description and the validation of project and suffix."""

from budtestlibrary import BloomMetaData, BudTestCase, parameterized
from tests import support

BAD_SUFFIXES = {
    "hashes": "##invalid##",
    "space inside": "0 1",
    "slash": "a/b",
    "non-ASCII letter": "ü1",
    "trailing newline": "001\n",
}


class BloomMetadata(BudTestCase):
    """BloomMetaData: the test case id and URL it builds, its dictionary, and the fields it refuses."""

    def bud_full_tc_id_format(self):
        """The full id is <project>-TC-<suffix>."""
        support.check(
            self,
            BloomMetaData(project="PRJ", tc_id_suffix="001").get_full_tc_id(),
            "PRJ-TC-001",
            "BloomMetaData(PRJ, 001) gives the full test case id PRJ-TC-001",
            "BloomMetaData(PRJ, 001) does not give the full test case id PRJ-TC-001",
        )

    def bud_url_with_configurable_base(self):
        """get_url() drops the base URL's trailing slash and appends the test case path."""
        url = BloomMetaData(project="PRJ", tc_id_suffix="001").get_url(
            base_url="https://custom-bloom.example.com/"
        )
        support.check(
            self,
            url,
            "https://custom-bloom.example.com/projects/PRJ/test-cases/001",
            "get_url() drops the trailing slash of the base URL and appends /projects/PRJ/test-cases/001",
            "get_url() with base https://custom-bloom.example.com/ does not give .../projects/PRJ/test-cases/001",
        )

    def bud_url_defaults_to_empty_base(self):
        """Without a base URL, and with an empty one, get_url() gives the path alone."""
        bm = BloomMetaData(project="PRJ", tc_id_suffix="001")
        support.check(
            self,
            bm.get_url(),
            "/projects/PRJ/test-cases/001",
            "get_url() without a base URL gives the path /projects/PRJ/test-cases/001",
            "get_url() without a base URL does not give the path /projects/PRJ/test-cases/001",
        )
        support.check(
            self,
            bm.get_url(base_url=""),
            "/projects/PRJ/test-cases/001",
            "get_url() with an empty base URL gives the path /projects/PRJ/test-cases/001",
            "get_url() with an empty base URL does not give the path /projects/PRJ/test-cases/001",
        )

    def bud_to_dict(self):
        """to_dict() holds project, tc_id, display_id, description and the URL path."""
        d = BloomMetaData(project="PRJ", tc_id_suffix="002", description="A test case").to_dict()
        want = {
            "project": "PRJ",
            "tc_id": "PRJ-TC-002",
            "display_id": "PRJ-TC-002",
            "description": "A test case",
            "url": "/projects/PRJ/test-cases/002",
        }
        support.check(
            self,
            d,
            want,
            "to_dict() holds project, tc_id, display_id, description and url for PRJ-TC-002",
            "to_dict() for PRJ-TC-002 differs from the expected project, tc_id, display_id, description and url",
        )

    def bud_optional_description(self):
        """The description defaults to None, in the object and in to_dict()."""
        bm = BloomMetaData(project="PRJ", tc_id_suffix="X")
        support.check(
            self,
            bm.description,
            None,
            "BloomMetaData without a description has description None",
            "BloomMetaData without a description has a description other than None",
        )
        support.check(
            self,
            bm.to_dict()["description"],
            None,
            "to_dict() of a BloomMetaData without a description holds description None",
            "to_dict() of a BloomMetaData without a description holds a description other than None",
        )

    @parameterized(["empty", "blank"])
    def bud_field_validation_rejects_empty_project(self, kind):
        """An empty or whitespace-only project raises ValueError."""
        project = "" if kind == "empty" else "   "
        exc = support.raised(BloomMetaData, project=project, tc_id_suffix="001")
        support.check(
            self,
            support.raised_name(exc),
            "ValueError",
            f"BloomMetaData refuses a project that is {kind} with ValueError",
            f"BloomMetaData did not refuse a project that is {kind} with ValueError",
        )

    @parameterized(["empty", "blank"])
    def bud_field_validation_rejects_empty_suffix(self, kind):
        """An empty or whitespace-only suffix raises ValueError."""
        suffix = "" if kind == "empty" else "   "
        exc = support.raised(BloomMetaData, project="PRJ", tc_id_suffix=suffix)
        support.check(
            self,
            support.raised_name(exc),
            "ValueError",
            f"BloomMetaData refuses a test case suffix that is {kind} with ValueError",
            f"BloomMetaData did not refuse a test case suffix that is {kind} with ValueError",
        )

    @parameterized(list(BAD_SUFFIXES))
    def bud_field_validation_rejects_invalid_suffix_format(self, kind):
        """A suffix with anything but ASCII letters, digits, _ and - is refused when the suite is written: no result is reported under a test case id that matches nothing in Bloom."""
        suffix = BAD_SUFFIXES[kind]
        exc = support.raised(BloomMetaData, project="PRJ", tc_id_suffix=suffix)
        support.check(
            self,
            support.raised_name(exc),
            "ValueError",
            f"BloomMetaData refuses the suffix {suffix!r} ({kind}), so no result is reported under the test case id {'PRJ-TC-' + suffix!r}, which no Bloom test case can have",
            f"BloomMetaData accepted the suffix {suffix!r} ({kind}): results would be reported under the test case id {'PRJ-TC-' + suffix!r}, which matches no test case in Bloom",
        )
