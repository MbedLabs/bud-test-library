"""Release metadata in pyproject.toml, the changelog entry of the declared version, README content, and the organisation and maintainer named by PACKAGE_ORG and ORG_MAINTAINER."""

import os
import re

import tomllib

import budtestlibrary
from budtestlibrary import BudTestCase
from tests import support

ORG = os.environ.get("PACKAGE_ORG", "")
MAINTAINER = os.environ.get("ORG_MAINTAINER", "")


def project() -> dict:
    """Return the [project] table of the code base's pyproject.toml."""
    return tomllib.loads((support.REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def readme() -> str:
    """Return the code base's README.md."""
    return (support.REPO / "README.md").read_text(encoding="utf-8")


class PackagingMetadata(BudTestCase):
    """The release metadata, changelog entry and README of the package."""

    def bud_the_declared_version_is_a_release_number(self):
        """The declared version is major.minor.patch and is the version the package reports."""
        version = project()["version"]
        support.check(
            self,
            bool(re.fullmatch(r"\d+\.\d+\.\d+", version)),
            True,
            f"the declared version {version} has the form major.minor.patch",
            f"the declared version {version} does not have the form major.minor.patch",
        )
        support.check(
            self,
            budtestlibrary.__version__,
            version,
            "budtestlibrary.__version__ is the version declared in pyproject.toml",
            "budtestlibrary.__version__ differs from the version declared in pyproject.toml",
        )

    def bud_release_metadata_names_the_org_urls_license_and_classifier(self):
        """Authors, maintainers, project URLs, license table and the production classifier."""
        meta = project()
        support.check(
            self,
            meta["authors"][0],
            {"name": "EmbedLabs", "email": "dev@embedlabs.net"},
            "the first author in pyproject.toml is EmbedLabs <dev@embedlabs.net>",
            "the first author in pyproject.toml is not EmbedLabs <dev@embedlabs.net>",
        )
        support.check(
            self,
            len(meta["authors"]),
            2,
            "pyproject.toml lists two authors",
            "pyproject.toml does not list exactly two authors",
        )
        support.check(
            self,
            meta["maintainers"],
            [{"name": "EmbedLabs", "email": "dev@embedlabs.net"}],
            "EmbedLabs <dev@embedlabs.net> is the only maintainer in pyproject.toml",
            "the maintainers in pyproject.toml are not only EmbedLabs <dev@embedlabs.net>",
        )
        support.check(
            self,
            meta["urls"],
            {
                "Homepage": "https://embedlabs.net",
                "Documentation": "https://embedlabs.net/docs",
                "Changelog": "https://embedlabs.net/docs",
                "Support": "https://embedlabs.net",
            },
            "pyproject.toml declares the Homepage, Documentation, Changelog and Support URLs on embedlabs.net",
            "the project URLs in pyproject.toml differ from the expected embedlabs.net addresses",
        )
        support.check(
            self,
            meta["license"],
            {"text": "AGPL-3.0-only"},
            "pyproject.toml declares the license AGPL-3.0-only",
            "pyproject.toml declares another license than AGPL-3.0-only",
        )
        support.check_in(
            self,
            "Development Status :: 5 - Production/Stable",
            meta["classifiers"],
            "pyproject.toml carries the classifier Development Status :: 5 - Production/Stable",
            "pyproject.toml lacks the classifier Development Status :: 5 - Production/Stable",
        )

    def bud_the_changelog_has_an_entry_for_the_declared_version(self):
        """CHANGELOG.md has a section for the declared version."""
        changelog = (support.REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        support.check_in(
            self,
            f"## [{project()['version']}]",
            changelog,
            f"CHANGELOG.md has a section for the declared version {project()['version']}",
            f"CHANGELOG.md has no section for the declared version {project()['version']}",
        )

    def bud_readme_marks_qt_client_as_roadmap_only(self):
        """The README marks pybudgui as planned and keeps the quick-start lines."""
        text = readme()
        for phrase in (
            "planned on the roadmap",
            "- **pybudgui**:",
            'bloom_metadata = BloomMetaData("PRJ", "001")  # Optional: attach Bloom traceability metadata',
            "### Optional Bloom Traceability",
            "def setUpClass(self):",
            "def tearDownClass(self):",
            "def bud_check_response(self):",
        ):
            support.check_in(
                self,
                phrase,
                text,
                f"the README holds {phrase!r}",
                f"the README lacks {phrase!r}",
            )

    def bud_readme_has_no_relative_markdown_links_that_break_on_pypi(self):
        """The README holds no relative Markdown link."""
        relative = re.findall(r"\[[^]]+\]\((?!https?://|mailto:|#)[^)]+\)", readme())
        support.check(
            self,
            relative,
            [],
            "the README holds no relative Markdown link, which would break on PyPI",
            "the README holds relative Markdown links, which break on PyPI",
        )

    def bud_the_package_names_its_org(self):
        """The organisation in PACKAGE_ORG is the first author and the only maintainer."""
        if not ORG:
            self.skipAssert("PACKAGE_ORG is not set")
            return
        meta = project()
        support.check(
            self,
            meta["authors"][0]["name"],
            ORG,
            f"the organisation {ORG} from PACKAGE_ORG is the first author",
            f"the organisation {ORG} from PACKAGE_ORG is not the first author",
        )
        support.check(
            self,
            [m["name"] for m in meta["maintainers"]],
            [ORG],
            f"the organisation {ORG} is the only maintainer",
            f"the organisation {ORG} is not the only maintainer",
        )

    def bud_the_package_names_its_maintainer(self):
        """The person in ORG_MAINTAINER is the author after the organisation."""
        if not MAINTAINER:
            self.skipAssert("ORG_MAINTAINER is not set")
            return
        support.check(
            self,
            project()["authors"][1:],
            [{"name": MAINTAINER}],
            f"{MAINTAINER} from ORG_MAINTAINER is the author after the organisation",
            f"the authors after the organisation are not only {MAINTAINER} from ORG_MAINTAINER",
        )

    def bud_readme_credits_its_maintainer(self):
        """The README credits the person in ORG_MAINTAINER."""
        if not MAINTAINER:
            self.skipAssert("ORG_MAINTAINER is not set")
            return
        support.check_in(
            self,
            f"Creator: {MAINTAINER}",
            readme(),
            f"the README credits {MAINTAINER} with the line Creator: {MAINTAINER}",
            f"the README lacks the line Creator: {MAINTAINER}",
        )
