# budtestlibrary

Universal Python test automation framework for HIL, SIL, web, mobile, cloud,
API, security, performance, and end-to-end testing.

It provides lifecycle management, rich assertions, structured results, logging,
firmware-flashing abstractions, and optional Bloom PLM integration through
`BloomMetaData` attached to test classes.

Creator: Amine El Omari

## Requirements

- Python 3.9 or later
- No required runtime dependencies

## Installation

```bash
python -m pip install budtestlibrary
```

## Features

- `BudTestCase` lifecycle with `setUpClass()` and `tearDownClass()`.
- Automatic discovery of methods whose names start with `bud_`.
- Boolean, equality, membership, range, tolerance, and regex assertions.
- Structured assertion and test-method results.
- Configurable source-location, traceback, and value capture.
- Coloured console output and plain serialised result data.
- Firmware flashing through `FlashEvent`, `FlashSuccess`, and `FlashFailure`.
- Environment-variable and `app.properties` configuration.
- Bundled examples for HIL, SIL, API, UI, cloud/E2E, and flashing scenarios.
- Optional Bloom PLM traceability with `BloomMetaData`.

## Quick start

```python
import logging

from budtestlibrary import BloomMetaData, BudTestCase


class MyTest(BudTestCase):
    bloom_metadata = BloomMetaData("PRJ", "001")  # Optional: attach Bloom traceability metadata

    def setUpClass(self):
        self.log_info("Setting up test")

    def bud_check_response(self):
        response = get_response()
        self.assertTrue(response.ok, msg="Response is successful")

    def bud_validate_output(self):
        result = compute_result()
        self.assertInTolerance(
            result,
            expected=42.0,
            absolute_tolerance=0.5,
            msg="Output is within tolerance",
        )

    def tearDownClass(self):
        self.log_info("Tearing down test")


if __name__ == "__main__":
    test = MyTest()
    test.set_loglevel(logging.INFO)
    test.run()
```

### Optional Bloom Traceability

`BloomMetaData` optionally links a test class to a Bloom test case using the
`{Project}-TC-{ID}` convention:

```python
from budtestlibrary import BloomMetaData, BudTestCase


class TraceableTest(BudTestCase):
    bloom_metadata = BloomMetaData("PRJ", "001")
```

This integration is optional. Tests run normally without Bloom metadata or a
Bloom deployment. When results flow through `bud_runner` into Bud, Bud uses the
metadata when the corresponding Bud project is linked to Bloom.

## Public API

| Export | Purpose |
|---|---|
| `BudTestCase` | Base class for lifecycle, assertions, logging, and results |
| `BloomMetaData` | Optional Bloom PLM test-case traceability metadata |
| `FlashEvent` | Abstract firmware-flashing operation |
| `FlashSuccess` | Successful flashing result |
| `FlashFailure` | Failed flashing result with error information |
| `BudConfig` | Configuration loaded from environment and properties |
| `get_default_config()` | Shared lazy-loaded configuration instance |

## Test structure

`BudTestCase.run()` discovers methods prefixed with `bud_` and executes them in
alphabetical order. Prefix methods numerically when explicit ordering matters:

```python
class OrderedTest(BudTestCase):
    def bud_01_connect(self):
        ...

    def bud_02_measure(self):
        ...
```

After execution, call `get_results()`:

```python
test = MyTest()
test.run()

for method_result in test.get_results():
    print(method_result.method_name, method_result.passed)
```

## Assertions

Available helpers include:

- `assertTrue` / `assertFalse`
- `assertEqual` / `assertNotEqual`
- `assertGreater` / `assertLess`
- `assertIn` / `assertNotIn`
- `assertRegex`
- `assertInTolerance`
- `assertInRange`
- `skipAssert`

Example:

```python
self.assertInRange(
    actual=temperature,
    lower_bound=18.0,
    upper_bound=26.0,
    include_bounds=True,
    msg="Temperature is inside the accepted range",
)
```

## Result capture

Subclass attributes control serialised result size and detail:

| Attribute | Default | Purpose |
|---|---:|---|
| `CAPTURE_SOURCE_PATH` | `True` | Capture failure source file and line |
| `CAPTURE_TRACEBACK` | `True` | Capture traceback text |
| `MAX_RESULT_VALUE_LENGTH` | `5000` | Truncate long expected/actual/result values |

```python
class CompactResultsTest(BudTestCase):
    CAPTURE_SOURCE_PATH = False
    CAPTURE_TRACEBACK = False
    MAX_RESULT_VALUE_LENGTH = 500
```

## Firmware flashing

Implement `FlashEvent` for product-specific flashing:

```python
from budtestlibrary import FlashEvent, FlashSuccess


class MyFlashEvent(FlashEvent):
    def flash(self, firmware_path):
        perform_flash(firmware_path)
        return FlashSuccess(message="Flashed successfully")

    def get_project_name(self):
        return "SensorHub"

    def get_firmware_version(self):
        return "2.1.0"

    def get_release(self):
        return "production"
```

## Configuration

```bash
export BUD_BACKEND_URL="https://<your-bud-instance-url>"
export BUD_TOKEN="<user-token>"
```

```properties
budBackend=https://<your-bud-instance-url>
budRunnerAccount=lab-station-01
```

Keep secrets outside repositories.

## Bundled examples

Examples ship inside the wheel under `budtestlibrary.examples`.

```bash
python -c "import budtestlibrary.examples, pathlib; print(pathlib.Path(budtestlibrary.examples.__file__).parent)"
```

| Example | Scenario |
|---|---|
| [`minimal_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/minimal_test.py) | Minimal test with core assertions |
| [`bloom_metadata_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/bloom_metadata_test.py) | Optional Bloom traceability |
| [`flash_event_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/flash_event_example.py) | Firmware flashing |
| [`hil_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/hil_test.py) | Hardware-in-the-loop |
| [`sil_test.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/sil_test.py) | Software-in-the-loop |
| [`api_testing_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/api_testing_example.py) | API testing |
| [`ui_testing_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/ui_testing_example.py) | UI testing |
| [`cloud_e2e_example.py`](https://github.com/MbedLabs/bud-test-library/blob/main/budtestlibrary/examples/cloud_e2e_example.py) | Cloud and E2E testing |

## Compatibility

| `budtestlibrary` | Intended `bud_runner` pairing | Notes |
|---|---|---|
| `1.0.2` | `1.0.2` | Permanent AGPL wording clarified; examples and README coverage expanded |
| `1.0.1` | `1.0.1` | Examples bundled in the wheel |
| `1.0.0.post2` | `1.0.0.post2` | Configurable capture, flashing abstractions, and separated test-software metadata |

## Development

```bash
git clone https://github.com/MbedLabs/bud-test-library.git
cd bud-test-library
python -m pip install -e ".[dev]"

black --check budtestlibrary/ examples/
isort --profile black --check-only budtestlibrary/ examples/
ruff check budtestlibrary/ examples/
mypy budtestlibrary/
pytest tests/ -v
```

## Related packages

- **bud_runner**: CLI tool for test execution and Bud integration.
- **pybudgui**: Python Qt desktop client for manual test execution, planned on the roadmap.

## Licence

`budtestlibrary` is permanent free and open-source software licensed under the
**GNU Affero General Public License v3.0 only (`AGPL-3.0-only`)**.

No paid EmbedLabs licence is required to use `budtestlibrary`, including for
commercial use, provided the AGPL terms are followed. Accepted community
contributions remain publicly available under `AGPL-3.0-only` and will not
become proprietary-only.

Bud and Bloom are separate source-available applications. Commercial licensing,
deployment, integration, and support offered through `sales@embedlabs.de`
applies to those applications and services—not to the `budtestlibrary` package
licence.

Technical, security, and contribution questions: `dev@embedlabs.net`.

Copyright (C) 2026 Mohamed Amine El Omari Alaoui, operating under the name
EmbedLabs.

- [Full licence](https://github.com/MbedLabs/bud-test-library/blob/main/LICENSE)
- [Contributing](https://github.com/MbedLabs/bud-test-library/blob/main/CONTRIBUTING.md)
- [Contributor License Agreement](https://github.com/MbedLabs/bud-test-library/blob/main/CLA.md)
