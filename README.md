# budtestlibrary

Universal test automation framework for HIL, SIL, Web, Mobile, Cloud, and E2E testing.
Provides a comprehensive test framework with lifecycle management, rich assertions, structured logging, and Bloom PLM integration.

Creator: Amine El Omari

## Table of Contents

- [Requirements](#requirements)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Public API](#public-api)
- [Test Structure](#test-structure)
- [Configuration](#configuration)
- [Logging & Console Output](#logging--console-output)
- [Assertions](#assertions)
- [Result Reporting Options](#result-reporting-options)
- [Result and Flash Abstractions](#result-and-flash-abstractions)
- [Result Schema](#result-schema)
- [Examples](#examples)
- [Compatibility](#compatibility)
- [Development Setup](#development-setup)
- [Related Packages](#related-packages)
- [License](#license)

## Requirements

- Python 3.9 or later

## Features

- **Lifecycle management** — `setUpClass`, `tearDownClass`, and auto-discovery of `bud_*` test methods.
- **Rich assertions** — boolean, equality, membership, range, tolerance, regex with structured result capture.
- **Bloom PLM traceability** — attach `BloomMetaData` to test classes for `{Project}-TC-{ID}` linkage.
- **Firmware flashing abstraction** — `FlashEvent` base class with `FlashSuccess` / `FlashFailure` result types and timing.
- **Colored console output** — multi-color pass/fail/skip formatting with bold timestamps and timezone.
- **Structured results** — `TestResult` (per-assertion) and `TestMethodResult` (per-step) with JSON serialization via `to_dict()`.
- **Configurable result capture** — opt-in source location, traceback, and value truncation to control payload size.
- **Configuration from env vars and properties files** — `BudConfig` loads from `BUD_*` environment variables and `app.properties`.
- **Bundled runnable examples** — HIL, SIL, API, UI, Cloud/E2E, and firmware flashing scenarios shipped in the wheel.
- **Zero required dependencies** — pure Python standard library; only optional dev/docs extras.

## Installation

```bash
pip install budtestlibrary
```

## Quick Start

```python
import logging
from budtestlibrary import BudTestCase, BloomMetaData

class MyTest(BudTestCase):
    bloom_metadata = BloomMetaData("PRJ", "001")  # Optional: attach Bloom traceability metadata

    def setUpClass(self):
        self.log_info("Setting up test...")

    def bud_check_response(self):
        response = get_response()
        self.assertTrue(response.ok, msg="Response is successful")

    def bud_validate_output(self):
        result = compute_result()
        self.assertInTolerance(
            result,
            expected=42.0,
            absolute_tolerance=0.5,
            msg="Output within expected range",
        )

    def tearDownClass(self):
        self.log_info("Tearing down test...")

if __name__ == "__main__":
    test = MyTest()
    test.set_loglevel(logging.INFO)
    test.run()
```

## Public API

All top-level exports from `budtestlibrary`:

| Export | Description |
|--------|-------------|
| `BudTestCase` | Base class for test cases with lifecycle, assertions, logging, and result collection |
| `BloomMetaData` | Dataclass linking a test class to a Bloom PLM test case (`{Project}-TC-{ID}`) |
| `FlashEvent` | Abstract base class for firmware flashing operations |
| `FlashSuccess` | Result dataclass for successful flash operations |
| `FlashFailure` | Result dataclass for failed flash operations with `error_code` and `recoverable` |
| `BudConfig` | Configuration container loaded from env vars and `app.properties` |
| `get_default_config()` | Returns the shared lazy-loaded `BudConfig` singleton |

## Test Structure

### The `bud_*` Method Convention

`BudTestCase.run()` auto-discovers any method whose name starts with `bud_` and executes it as a test step. Methods are discovered at runtime via `dir()` and sorted alphabetically, so you control execution order by naming (e.g., `bud_01_connect`, `bud_02_verify`, etc.).

### Lifecycle Hooks

Override these methods on your test class:

| Hook | Called |
|------|--------|
| `setUpClass()` | Once, before any `bud_*` methods |
| `tearDownClass()` | Once, after all `bud_*` methods complete (always called, even on failure) |

### Retrieving Results

After `run()` completes, call `get_results()` to retrieve the list of `TestMethodResult` objects:

```python
test = MyTest()
test.run()
for r in test.get_results():
    print(f"{r.method_name}: {'PASS' if r.passed else 'FAIL'} ({r.duration_seconds:.2f}s)")
    for a in r.assertions:
        print(f"  [{a.assertion_type}] {a.message} — passed={a.passed}")
```

### Optional Bloom Traceability

Optionally, attach `BloomMetaData` to the test class for Bud/Bloom traceability on reported results:

```python
from budtestlibrary import BudTestCase, BloomMetaData

class TraceableTest(BudTestCase):
    bloom_metadata = BloomMetaData("PRJ", "001")
```

## Configuration

Configure via environment variables or `app.properties`:

### Environment Variables

```bash
export BUD_BACKEND_URL="https://<your-bud-instance-url>/"
export BUD_TOKEN="your-api-token"
```

### app.properties

```properties
budBackend=https://<your-bud-instance-url>/
budRunnerAccount=my-runner
```

## Assertions

### assertTrue / assertFalse

```python
self.assertTrue(condition, msg="Description", abort_on_fail=False)
self.assertFalse(condition, msg="Description")
```

### assertEqual / assertNotEqual

```python
self.assertEqual(actual, expected, msg="Description")
self.assertNotEqual(actual, expected, msg="Description")
```

### assertGreater / assertLess

```python
self.assertGreater(actual, expected, msg="Description")
self.assertLess(actual, expected, msg="Description")
```

### assertIn / assertNotIn

```python
self.assertIn(member=2, container=[1, 2, 3], msg="Description")
self.assertNotIn(member=99, container=[1, 2, 3], msg="Description")
```

### assertRegex

```python
self.assertRegex(text="hello world", pattern=r"hello", msg="Description")
```

### assertInTolerance

```python
self.assertInTolerance(
    actual,
    expected,
    absolute_tolerance=0.1,      # ±0.1
    relative_tolerance=0.05,     # ±5%
    msg="Description",
)
```

### assertInRange

```python
self.assertInRange(
    actual,
    lower_bound=0.0,
    upper_bound=10.0,
    include_bounds=True,
    msg="Description",
)

# upper_bound is optional — checks >= lower_bound when omitted
self.assertInRange(
    actual,
    lower_bound=5.0,
    msg="Description",
)
```

### skipAssert

```python
self.skipAssert(msg="Skipping: hardware not available")
```

Records a skipped assertion in results without failing. Useful for conditional test logic where a check is not applicable in the current environment.

## Result Reporting Options

Subclass attributes on `BudTestCase` control what is stored in assertion and method results (and serialized via `to_dict()`):

| Attribute | Default | Description |
|-----------|---------|-------------|
| `CAPTURE_SOURCE_PATH` | `True` | When `True`, failed assertions record `source_file`, `source_line`, and `source_function` from the call site. Set to `False` to omit source location (smaller payloads). |
| `CAPTURE_TRACEBACK` | `True` | When `True`, tracebacks are attached to failed assertions and method results. Set to `False` to omit traceback strings from stored results. |
| `MAX_RESULT_VALUE_LENGTH` | `5000` | Maximum character length for `expected`, `actual`, and `result` strings in `TestResult.to_dict()`. Longer values are truncated with `"... <truncated>"`. |

```python
class CompactResultsTest(BudTestCase):
    CAPTURE_SOURCE_PATH = False
    CAPTURE_TRACEBACK = False
    MAX_RESULT_VALUE_LENGTH = 500

    def bud_check(self):
        self.assertTrue(True, msg="minimal result payload")
```

## Result and Flash Abstractions

### TestMethodResult

The result objects include detailed failure and summary messages:

- `error_message`: Richly formatted with the exact assertion line when failed.
- `summary_message`: Concisely summarizes the execution (e.g., `"Passed: N assertion(s) in M.Ns"` or mirrors `error_message` on failure).

### FlashEvent

`FlashEvent` is an abstract base class for firmware flashing. Implement `flash()`, `get_project_name()`, `get_firmware_version()`, and `get_release()`:

```python
class MyFlashEvent(FlashEvent):
    def flash(self, firmware_path):
        ...
        return FlashSuccess(message="Flashed OK")

    def get_project_name(self):
        return "ESP32-SensorHub"

    def get_firmware_version(self):
        return "2.1.0"

    def get_release(self):
        return "production"

event = MyFlashEvent()
result = event.execute("/path/to/firmware.bin")
print(event.get_info())
```

### FlashFailure

`FlashFailure` defaults to a `message` key (matching `FlashSuccess`), while preserving a read-only `error_message` property for backward compatibility. Its `to_dict()` keys include `message`, `error_message`, `error_code`, and `recoverable`.

## Result Schema

`budtestlibrary` produces two primary result shapes:

### `TestResult`

One assertion-level record. Serialized keys include:

- `passed`
- `message`
- `skipped`
- `assertion_type`
- `expected`
- `actual`
- `result`
- `source_file`
- `source_line`
- `source_function`
- `code_context`
- `traceback`
- `timestamp`
- `metadata`

### `TestMethodResult`

One `bud_*` method-level record. Serialized keys include:

- `method_name`
- `passed`
- `skipped`
- `assertions`
- `duration_seconds`
- `error_message`
- `summary_message`
- `traceback`
- `metadata`

In a typical integration, `bud_runner` flattens these method-level results into the payload it uploads to Bud TMP while preserving assertion detail.

## Examples

Runnable example scenarios are **bundled with the package** and installed alongside it:

```bash
# Find the installed examples directory
python -c "import budtestlibrary.examples; import pathlib; print(pathlib.Path(budtestlibrary.examples.__file__).parent)"
```

| File | Scenario |
|------|----------|
| [`minimal_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/minimal_test.py) | Smallest possible `BudTestCase` with all core assertions |
| [`bloom_metadata_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/bloom_metadata_test.py) | Bloom PLM traceability metadata on test results |
| [`flash_event_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/flash_event_example.py) | Firmware flashing with `FlashEvent`, `FlashSuccess`, and `FlashFailure` |
| [`hil_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/hil_test.py) | Hardware-in-the-loop checks against a target board |
| [`sil_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/sil_test.py) | Software-in-the-loop logic validation |
| [`api_testing_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/api_testing_example.py) | Service/API assertions with response payload checks |
| [`ui_testing_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/ui_testing_example.py) | UI-style assertions for page state and user feedback |
| [`cloud_e2e_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/cloud_e2e_example.py) | Cloud / end-to-end test flow with latency checks |

## Compatibility

| `budtestlibrary` | Intended `bud_runner` pairing | Notes |
|------------------|--------------------------------|-------|
| `1.0.2` | `1.0.2` | Commercial licensing wording updated; examples test coverage added; README expanded |
| `1.0.1` | `1.0.1` | Examples bundled in wheel; no API changes |
| `1.0.0.post2` | `1.0.0.post2` | Supports configurable traceback/source capture, result truncation, `FlashEvent`, and separate `test_software` vs `software_under_test` metadata in the runner flow |

## Development Setup

```bash
# Clone and install with dev extras
git clone <repo-url>
cd budtestlibrary
pip install -e ".[dev]"

# Lint
black --check budtestlibrary/ examples/
isort --profile black --check-only budtestlibrary/ examples/
ruff check budtestlibrary/ examples/
mypy budtestlibrary/

# Run tests
pytest tests/ -v
```

## Related Packages

- **bud_runner**: CLI tool for test execution and CI/CD integration
- **pybudgui**: A python-based Qt desktop client for manual test execution (planned on the roadmap)

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. Full license text: https://www.gnu.org/licenses/agpl-3.0.html

Copyright (C) 2026 EmbedLabs.

For commercial licensing of the hosted Bud (Test Management Platform) and Bloom (Product Lifecycle Management) applications that do not require AGPL compliance, contact sales@embedlabs.de. For support or private-source collaboration, email dev@embedlabs.net.
