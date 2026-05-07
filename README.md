# budtestlibrary

Universal test automation framework for HIL, SIL, Web, Mobile, Cloud, and E2E testing.

## Overview

`budtestlibrary` provides a comprehensive test framework with lifecycle management, rich assertions, logging, and Bloom PLM integration:

- **BudTestCase**: Base class for test cases with lifecycle hooks, rich assertions, and logging
- **BloomMetaData**: Link tests to Bloom PLM test cases for traceability
- **FlashEvent**: Standardized firmware flashing abstraction
- **BloomSync**: Automatic synchronization of test cases and results to Bloom PLM

## Installation

To use `budtestlibrary` in your projects, add it as a submodule:

```bash
git submodule add https://github.com/MbedLabs/bud-test-library.git
pip install -e ./bud-test-library
```

## Quick Start

```python
import logging
from budtestlibrary import BudTestCase, BloomMetaData

class MyTest(BudTestCase):
    bloom_metadata = BloomMetaData("my-project", "001")

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
export BLOOM_URL="https://<your-bloom-instance-url>/"
export BLOOM_TOKEN="your-bloom-jwt-token"
export BLOOM_EMAIL="user@<your-domain>.de"
export BLOOM_PASSWORD="your-password"
```

### app.properties

```properties
budBackend=https://<your-bud-instance-url>/
bloomUrl=https://<your-bloom-instance-url>/
budRunnerAccount=my-runner
runnerSocketPort=53035
```

## Assertions

### assertTrue
```python
self.assertTrue(condition, msg="Description", abort_on_fail=False)
```

### assertEqual
```python
self.assertEqual(actual, expected, msg="Description")
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
```

## Bloom PLM Integration

Sync test cases to Bloom PLM:

```python
from budtestlibrary import BloomSync

sync = BloomSync()

sync.sync_test_suite(
    project_identifier="my-project",
    campaign_name="Integration Tests",
    test_classes=[MyTest, AnotherTest],
)

sync.update_test_result(
    campaign_id=1,
    test_case_id=42,
    passed=True,
)
```

## JUnit XML Output

Generate JUnit XML for CI/CD integration:

```python
test = MyTest()
test.run()

with open("report_junit.xml", "w") as f:
    f.write(test.to_junit_xml())
```

## Related Packages

- **bud_runner**: CLI tool for test execution and CI/CD integration
- **pybudgui**: PyQt6 desktop application for manual testing and result visualization

## License

This project is licensed under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**. See the [LICENSE](LICENSE) file for the full text.

Copyright (C) 2024-2026 EmbedLabs.

For commercial licensing options that do not require AGPL compliance, contact dev@embedlabs.de. Contributions are accepted under the [CLA](CLA.md) — see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
