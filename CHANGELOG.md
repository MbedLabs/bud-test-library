# Changelog

All notable changes to `budtestlibrary` will be documented in this file.

## [1.3.0] - unreleased

### Changed
- Python 3.11 or later is required; Python 3.9 and 3.10 are no longer supported.

## [1.2.0] — 2026-10-15

### Added
- `attach_artifact(path, name=None)` records an existing file on the current step's result as `metadata["artifacts"]`, a list of `{"path": <absolute path>, "name": <name or file name>}`, present only on steps that attached a file. Inside a step, a path that is not an existing file records a failed `AttachArtifact` entry and stops the step; inside `setUp()` it is a setup failure and inside `tearDown()` it is logged, as for other errors in those hooks. A call from `setUpClass()` or `tearDownClass()` is not recorded; a missing file in `setUpClass()` fails the run like any other `setUpClass()` error.
- `waitUntil(condition_fn, timeout=10.0, poll_interval=0.5, msg="", abort_on_fail=False)` polls a condition until it is true or the timeout passes, returns whether it was met and records an `AssertWaitUntil` entry with `elapsed_seconds`, `timeout_seconds` and `poll_interval_seconds` in its metadata. An exception from the condition counts as not yet true; on timeout the last one is recorded as `last_exception`.
- `require(condition, msg="", **kwargs)` records an `AssertRequire` entry and, when the condition is false, raises `AssertionError` so the step stops at once.
- `assertRaises(expected_exception, msg="", abort_on_fail=False)` context manager records an `AssertRaises` entry: passed when the block raises the expected exception (or a subclass), failed when it raises nothing or a different exception, which is then suppressed. With `abort_on_fail=True` a failure raises `AssertionError`. An unexpected exception that is not an `Exception` subclass (such as `KeyboardInterrupt`, `SystemExit` or `asyncio.CancelledError`) passes through unrecorded.
- `async def bud_` steps, parameterized ones included, run to completion with `asyncio.run()`; their assertions and unhandled exceptions are recorded like those of any step. A step called from inside an already running event loop fails with the `RuntimeError` from `asyncio.run()`.
- `setUp()` and `tearDown()` on `BudTestCase` run before and after each `bud_` step; `tearDown()` runs even when the step fails. Assertions called inside them are logged but not recorded on the step. An aborting assertion in `setUp()` is a setup error. Existing subclass overrides of these hooks now run once per step. A `setUp()` error skips the step and fails it with `setUp failed: <error>`; a `tearDown()` error is logged and leaves the step result unchanged. Their log lines appear at DEBUG level. A step's `duration_seconds` covers `setUp()`, the method and `tearDown()`.
- `@parameterized(data)` runs a `bud_` method once per data item as separate steps named `<method>[<id>]`, each with its own result; a single value is passed as one argument, a tuple as positional arguments, a dict as keyword arguments. A failing item does not stop the others. All step names, plain or parameterized, must fit within 255 characters; parameterized names must also be unique. An invalid name fails the run after `setUpClass()` and before any step executes. Exported from `budtestlibrary`.

### Changed
- Assertion source capture walks the call frames; `inspect.stack()` is no longer called. Source file, line and function are recorded as before; source lines (`code_context`) and the traceback are built only for a failed assertion, so a passing assertion no longer carries `code_context`.
- `bud_` methods run in the order they are declared in the test class instead of alphabetical order, so numeric prefixes are no longer needed to order steps. A subclass's own methods run before inherited ones; an override runs in the subclass's position. A suite whose methods are declared in a different order than their alphabetical one now runs in the declared order. Methods are found on the class and its bases; a `bud_` attribute set on an instance is no longer run.

## [1.1.0] — 2026-09-09

### Added
- `budtestlibrary check <path>` reports the Bloom test cases a suite claims, before it runs. A `tc_id` is typed by hand, and a wrong one is only noticed after the fact: Bloom returns it as unmatched, Bud records a warning on the run, and the run stays green while the test case reads as never executed. A duplicate is quieter still: two classes claiming one id are coalesced into a single result, and one outcome replaces the other. The command reports both, along with classes that claim nothing and modules it could not import, and exits non-zero on a duplicate so a pipeline fails on the error. `--list` prints the `tc_id` to test class map, `--json` emits it for CI, `--strict` also fails on an untraced class.

  It talks to nothing, and cannot tell whether an id exists in Bloom: this library holds no Bloom address and no credential.

### Changed
- The packaging test pins the version as a release number rather than a literal, which was a hand edit every release.

## [1.0.3] — 2026-08-16

### Added
- `FlashEvent.flash()` and `FlashEvent.execute()` accept an optional `addr`
  target memory address (e.g. `0x08000000` on STM32, `0x10000` on ESP32);
  `None` means the implementation's platform default
- Test coverage for the optional `addr` argument, including positional and
  keyword forwarding and legacy-signature compatibility

### Changed
- `execute()` detects whether an implementation's `flash()` accepts `addr`.
  Existing `flash(self, firmware_path)` subclasses keep working unchanged;
  passing an explicit `addr` to one returns a `FlashFailure` naming the class
  and the required signature change
- `flash_event_example` and README document the optional `addr` argument

## [1.0.2] — 2026-07-22

### Changed
- README expanded with public API, lifecycle, assertions, result capture, configuration, examples, and development guidance
- Optional Bloom PLM integration remains documented through `BloomMetaData`
- Package licensing wording now explicitly confirms that `budtestlibrary` remains free and open source under `AGPL-3.0-only`, including for commercial use subject to AGPL compliance
- Bud and Bloom application licensing is clearly separated from the `budtestlibrary` package licence
- Contributor terms now guarantee that Accepted Contributions remain publicly available under `AGPL-3.0-only`
- Pull requests now include an explicit CLA acceptance declaration

### Added
- Test coverage for bundled `budtestlibrary.examples` modules, including import, script execution, and result validation
- `#`-prefixed anchor links allowed in README relative-link validation for PyPI compatibility

## [1.0.1] — 2026-07-19

### Changed
- Examples are bundled inside the wheel as the `budtestlibrary.examples` subpackage
- README includes instructions for locating installed examples

## [1.0.0.post2] — 2026-06-28

### Changed
- Package version advanced to `1.0.0.post2` for final public metadata and documentation corrections
- Project URLs now point to `embedlabs.net`
- Quick-start example marks `BloomMetaData` as optional
- Optional Bloom traceability remains documented separately

## [1.0.0.post1] — 2026-06-28

### Changed
- Package version advanced to `1.0.0.post1` for a documentation-only PyPI correction
- Package author metadata now credits Amine El Omari
- README credits the creator and marks the Qt desktop client as roadmap-only

## [1.0.0] — 2026-06-28

### Added
- Release metadata regression coverage for version, licence metadata, and changelog alignment

### Changed
- Package version advanced to `1.0.0`
- Packaging metadata now uses a PEP 621-compatible licence table
- Release classifier moved from beta to production/stable
- Runtime version resolution prefers installed package metadata before local source metadata

## [0.3.0] — 2026-05-20

### Added
- New assertion methods: `assertFalse`, `assertNotEqual`, `assertGreater`, `assertLess`, and `assertRegex`
- Configurable source path and traceback capture
- `BloomMetaData` validation
- Result value truncation

### Changed
- `FlashFailure.message` became a required positional argument
- `BloomMetaData.get_url()` accepts a configurable base URL
- `assertIn` and `assertNotIn` raise `TypeError` for non-container arguments

### Fixed
- Zero absolute tolerance now requires an exact match
- `BudTestCase` no longer mutates the root logger
- Serialised result output remains plain text

### Removed
- `FlashStatus`; use `is_success()` instead

## [0.2.0] — 2025

### Added
- Initial public release
- `BudTestCase` lifecycle, assertions, and logging
- `BloomMetaData` for optional Bloom PLM integration
- `FlashEvent` firmware-flashing abstraction
- Environment-variable and `app.properties` configuration
