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

- `BudTestCase` lifecycle with `setUpClass()` and `tearDownClass()` once per class, and `setUp()` and `tearDown()` around each step.
- Automatic discovery of methods whose names start with `bud_`, run in declaration order.
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

### Checking what a suite claims

A `tc_id` is typed by hand. If it is wrong, Bloom reports it as unmatched, Bud
records a warning on the run, and nothing else happens — the run is green and the
test case reads as never executed. If two classes claim the same id, Bud coalesces
them into one result and one outcome silently replaces the other.

```bash
budtestlibrary check tests/
```

It imports the modules under that path, reads the id each test class claims, and
reports duplicates, classes claiming nothing, and modules it could not import. It
exits non-zero on a duplicate, so CI fails on the error rather than on a report
nobody reads.

```
✗ FLT-TC-001 is claimed by 2 test classes:
    tests/test_brakes.py::BrakePressureTest
    tests/test_thermal.py::ThermalSoakTest

2 test class(es): 2 claim 1 Bloom test case(s), 0 claim none, 1 id(s) duplicated.
```

`--list` prints the `tc_id` to test class map, `--json` emits the same report for a
pipeline, and `--strict` also fails when a test class claims no Bloom test case.

The command talks to nothing. It cannot tell whether `FLT-TC-001` exists in Bloom,
because this library holds no Bloom address and no credential.

## Public API

| Export | Purpose |
|---|---|
| `BudTestCase` | Base class for lifecycle, assertions, logging, and results |
| `parameterized` | Decorator that runs a `bud_` method once per data item |
| `BloomMetaData` | Optional Bloom PLM test-case traceability metadata |
| `FlashEvent` | Abstract firmware-flashing operation |
| `FlashSuccess` | Successful flashing result |
| `FlashFailure` | Failed flashing result with error information |
| `BudConfig` | Configuration loaded from environment and properties |
| `get_default_config()` | Shared lazy-loaded configuration instance |
| `budtestlibrary check` | Command that reports the Bloom test cases a suite claims |

## Test structure

`BudTestCase.run()` discovers methods prefixed with `bud_` and executes them in
the order they are declared in the class. No numeric prefixes are needed:

```python
class OrderedTest(BudTestCase):
    def bud_connect(self):
        ...

    def bud_measure(self):
        ...

    def bud_disconnect(self):
        ...
```

A subclass's own `bud_` methods run first, then the ones it inherits, base class
by base class. A method that overrides an inherited one runs in the subclass's
position.

Steps may be `async def`; each one is run to completion with `asyncio.run()`,
and its assertions and exceptions are recorded as for any step:

```python
class ApiTest(BudTestCase):
    async def bud_health(self):
        status = await fetch_status()
        self.assertEqual(status, 200)
```

### Per-step setup and cleanup

`setUp()` runs before each `bud_` step and `tearDown()` after it, even when the
step fails. Assertions called inside them are logged but not recorded on the
step; only one that aborts in `setUp()` (`abort_on_fail=True`) fails the step, as
a setup failure. If `setUp()` raises, the
step is not run and fails with `setUp failed: <error>`; `tearDown()` still runs.
An error in `tearDown()` is logged and does not change the step result. Their
enter and exit lines are logged at DEBUG level, shown after
`set_loglevel(logging.DEBUG)`.

```python
class DeviceTest(BudTestCase):
    def setUp(self):
        self.device = open_device()

    def tearDown(self):
        self.device.close()

    def bud_reads_temperature(self):
        self.assertInRange(self.device.temperature(), 18.0, 26.0)
```

### Parameterized steps

`@parameterized(data)` runs a `bud_` method once per item of `data`, each run a
separate step with its own result. A single value is passed as one argument, a
tuple is unpacked as positional arguments and a dict as keyword arguments:

```python
from budtestlibrary import BudTestCase, parameterized


class RailTest(BudTestCase):
    @parameterized(["1.8V", "3.3V"])
    def bud_test_voltage(self, rail):
        ...

    @parameterized([{"rail": "3.3V", "limit": 0.1}])
    def bud_test_ripple(self, rail, limit):
        ...
```

The steps are named `bud_test_voltage[1.8V]`, `bud_test_voltage[3.3V]` and
`bud_test_ripple[rail=3.3V, limit=0.1]` (tuple values are joined by `, `). They
run in the decorated method's position, in data order, and a failing item does
not stop the others. Step names must be unique and at most 255 characters (the
length Bud stores); a repeated or longer name fails the run after `setUpClass()`
and before any step executes.

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
    DEFAULT_ADDR = 0x08000000

    def flash(self, firmware_path, addr=None):
        perform_flash(firmware_path, self.DEFAULT_ADDR if addr is None else addr)
        return FlashSuccess(message="Flashed successfully")

    def get_project_name(self):
        return "SensorHub"

    def get_firmware_version(self):
        return "2.1.0"

    def get_release(self):
        return "production"
```

`addr` is the optional target memory address (for example `0x08000000` on
STM32, `0x10000` on ESP32). Pass it through `execute()` when a run needs a
specific address, and omit it to use the implementation's default:

```python
event = MyFlashEvent()
event.execute("firmware.bin")                     # implementation default
event.execute("bootloader.bin", addr=0x08000000)  # explicit address
```

Implementations that do not need an address may keep the single-argument
`flash(self, firmware_path)` signature — `execute()` detects this and calls
them unchanged. Passing an explicit `addr` to such an implementation returns a
`FlashFailure` explaining that `addr=None` must be added to its signature.

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
| `1.1.0` | `1.1.0` | Updated compatibility matrix |
| `1.0.3` | `1.0.3` | Optional `addr` target address on `FlashEvent.flash()` and `FlashEvent.execute()` |
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
