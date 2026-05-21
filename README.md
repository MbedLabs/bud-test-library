# budtestlibrary

Universal test automation framework for HIL, SIL, Web, Mobile, Cloud, and E2E testing.
It provides a comprehensive test framework with lifecycle management, rich assertions, logging, and Bloom PLM integration.

## Installation

```bash
pip install budtestlibrary
```

## Quick Start

```python
import logging
from budtestlibrary import BudTestCase, BloomMetaData

class MyTest(BudTestCase):
    bloom_metadata = BloomMetaData("PRJ", "001")

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
runnerSocketPort=53035
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

## Result capture options

Subclass attributes on `BudTestCase` control what is stored in assertion and method results (and serialized via `to_dict()`):

| Attribute | Default | Description |
|-----------|---------|-------------|
| `CAPTURE_SOURCE_PATH` | `True` | When `True`, failed assertions record `source_file`, `source_line`, and `source_function` from the call site. Set to `False` to omit source location (smaller payloads, less introspection overhead). |
| `CAPTURE_TRACEBACK` | `True` | When `True`, tracebacks are attached to failed assertions and method results where applicable. Set to `False` to omit traceback strings from stored results. |
| `MAX_RESULT_VALUE_LENGTH` | `5000` | Maximum character length for `expected`, `actual`, and `result` strings in `TestResult.to_dict()`. Longer values are truncated with `"... <truncated>"`. |

```python
class CompactResultsTest(BudTestCase):
    CAPTURE_SOURCE_PATH = False
    CAPTURE_TRACEBACK = False
    MAX_RESULT_VALUE_LENGTH = 500

    def bud_check(self):
        self.assertTrue(True, msg="minimal result payload")
```

Default shared configuration (backend URLs, tokens) is available via `get_default_config()` from `budtestlibrary` or `budtestlibrary.config` — it is created on first use, not at import time.

## Result and Flash Abstractions

### TestMethodResult
The result objects include detailed failure and summary messages:
- `error_message`: Richly formatted with the exact assertion line when failed.
- `summary_message`: Concisely summarizes the execution (e.g., "Passed: N assertion(s) in M.NNs" or mirrors `error_message` on failure).

### FlashFailure
Firmware flash results use a unified interface. `FlashFailure` defaults to a `message` key (matching `FlashSuccess`), while preserving a read-only `error_message` for backward compatibility. Its `to_dict()` keys include `message`, `error_message`, `error_code`, and `recoverable`.

### FlashEvent
Flash events accept a `firmware_path` parameter in both `flash()` and `execute()` methods:

```python
class MyFlashEvent(FlashEvent):
    def flash(self, firmware_path):
        ...
        return FlashSuccess()

event = MyFlashEvent()
result = event.execute("/path/to/firmware.hex")
```

## Related Packages

- **bud_runner**: CLI tool for test execution and CI/CD integration
- **pybudgui**: PyQt6 desktop application for manual testing and result visualization

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See the [LICENSE](LICENSE) file for the full text.

Copyright (C) 2026 EmbedLabs.

For commercial licensing options that do not require AGPL compliance, contact dev@embedlabs.net. Contributions are accepted under the [CLA](CLA.md) — see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
