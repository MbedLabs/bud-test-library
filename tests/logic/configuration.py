"""BudConfig and get_default_config(): no reads at import time, one shared instance, the package export, the properties-file warning and a bad number in the file."""

import logging
import os

from budtestlibrary import BudConfig, BudTestCase, get_default_config
from tests import support


class Records(logging.Handler):
    """A logging handler that keeps the messages it receives."""

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


class Configuration(BudTestCase):
    """BudConfig and get_default_config()."""

    def bud_not_instantiated_until_first_call(self):
        """Importing the package reads no properties file; the first get_default_config() call does."""
        cwd = support.work_dir("lazy-config")
        (cwd / "app.properties").mkdir()
        code = (
            "import logging, sys\n"
            "logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format='%(name)s %(message)s')\n"
            "import budtestlibrary\n"
            "print('imported', file=sys.stderr, flush=True)\n"
            "budtestlibrary.get_default_config()\n"
            "print('called', file=sys.stderr, flush=True)\n"
        )
        done = support.python("-c", code, cwd=cwd)
        lines = [line for line in done.err.splitlines() if line]
        support.check(
            self,
            done.code,
            0,
            "the child that imports budtestlibrary and calls get_default_config() exits 0",
            f"the child that imports budtestlibrary and calls get_default_config() did not exit 0: {done.err!r}",
        )
        support.check(
            self,
            lines[0],
            "imported",
            "importing budtestlibrary logs nothing before the import completes",
            "importing budtestlibrary logged a line, so a properties file was read at import time",
        )
        support.check(
            self,
            lines[1][: len("budtestlibrary.config Error loading properties file")],
            "budtestlibrary.config Error loading properties file",
            "the first get_default_config() call reads app.properties and logs that it cannot load it",
            "the first get_default_config() call did not log the properties-file error on budtestlibrary.config",
        )
        support.check(
            self,
            lines[2:],
            ["called"],
            "nothing else is logged after the first get_default_config() call",
            "more lines were logged after the first get_default_config() call",
        )

    def bud_returns_singleton(self):
        """Two calls return the same object."""
        support.check(
            self,
            get_default_config() is get_default_config(),
            True,
            "two get_default_config() calls return the same BudConfig object",
            "two get_default_config() calls returned two different objects",
        )

    def bud_exported_from_package(self):
        """get_default_config is exported by the package and returns a BudConfig."""
        import budtestlibrary

        support.check(
            self,
            budtestlibrary.get_default_config is get_default_config,
            True,
            "budtestlibrary exports get_default_config at package level",
            "budtestlibrary.get_default_config is not the get_default_config of budtestlibrary.config",
        )
        support.check(
            self,
            type(budtestlibrary.get_default_config()).__name__,
            "BudConfig",
            "budtestlibrary.get_default_config() returns a BudConfig",
            "budtestlibrary.get_default_config() returns another type than BudConfig",
        )

    def bud_load_warning_uses_logging(self):
        """An unreadable properties path logs a warning on budtestlibrary.config; a missing one logs nothing."""
        logger = logging.getLogger("budtestlibrary.config")
        records = Records()
        logger.addHandler(records)
        try:
            BudConfig(_properties_file=str(support.work_dir("missing-props") / "app.properties"))
            missing = list(records.messages)
            BudConfig(_properties_file=str(support.work_dir("dir-props")))
            unreadable = list(records.messages)
        finally:
            logger.removeHandler(records)
        support.check(
            self,
            missing,
            [],
            "BudConfig with a properties file that does not exist logs nothing",
            "BudConfig with a properties file that does not exist logged a line",
        )
        support.check(
            self,
            len(unreadable),
            1,
            "BudConfig with a properties path that is a directory logs exactly one line",
            "BudConfig with a properties path that is a directory did not log exactly one line",
        )
        support.check(
            self,
            unreadable[0][: len("Error loading properties file")],
            "Error loading properties file",
            "the logged line says Error loading properties file",
            "the logged line does not start with Error loading properties file",
        )

    def bud_bad_port_in_properties_keeps_the_default(self):
        """A non-numeric runnerSocketPort in the file keeps the default 53035 and raises nothing."""
        props = support.work_dir("bad-port") / "app.properties"
        props.write_text("runnerSocketPort=not-a-number\n")
        saved = os.environ.pop("BUD_RUNNER_SOCKET_PORT", None)
        try:
            config = BudConfig(_properties_file=str(props))
        finally:
            if saved is not None:
                os.environ["BUD_RUNNER_SOCKET_PORT"] = saved
        support.check(
            self,
            config.runner_socket_port,
            53035,
            "runnerSocketPort=not-a-number in app.properties keeps the default port 53035",
            "runnerSocketPort=not-a-number in app.properties changed the port from the default 53035",
        )
