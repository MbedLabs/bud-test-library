# budtestlibrary

Test automation framework for embedded systems testing.

## Overview

`budtestlibrary` provides a comprehensive test framework for hardware-in-loop (HIL) and functional component testing (FCT) of embedded systems. It offers:

- **BudTestCase**: Base class for test cases with lifecycle management, rich assertions, and logging
- **RequirementMetadata**: Link tests to Bloom ALM/Jira for requirement traceability
- **FlashEvent**: Standardized firmware flashing abstraction
- **BloomSync**: Automatic synchronization of test cases to Bloom ALM

## Installation

### From GitHub (submodule)

```bash
git submodule add https://github.com/embedlabs/budtestlibrary.git
pip install -e ./budtestlibrary
```

### From pip.embedlabs.de (coming soon)

```bash
pip install budtestlibrary --index-url https://pip.embedlabs.de/simple
```

## Quick Start

```python
import logging
from budtestlibrary import BudTestCase, RequirementMetadata

class MyBMSTest(BudTestCase):
    # Link to Bloom ALM requirement
    requirement_metadata = RequirementMetadata("bms-project", "REQ-1234")
    
    def setUpClass(self):
        # Initialize test resources
        self.log_info("Setting up BMS test...")
        # self.bms = MyBMSInterface()
    
    def mate_voltage_measurement(self):
        """Test voltage measurement accuracy."""
        measured_voltage = 3.7  # Read from hardware
        expected_voltage = 3.7
        
        self.assertInTolerance(
            measured_voltage,
            expected_voltage,
            absolute_tolerance=0.05,
            msg="Cell voltage measurement",
            cell=1,
        )
    
    def mate_current_limits(self):
        """Test current limiting functionality."""
        current = 10.5  # Read from hardware
        
        self.assertInRange(
            current,
            lower_bound=9.0,
            upper_bound=11.0,
            msg="Current within operating limits",
        )
    
    def tearDownClass(self):
        # Cleanup resources
        self.log_info("Tearing down BMS test...")
        # self.bms.shutdown()

if __name__ == "__main__":
    test = MyBMSTest()
    test.set_loglevel(logging.INFO)
    test.run()
```

## Configuration

Configure via environment variables or `app.properties`:

### Environment Variables

```bash
export BUD_BACKEND_URL="https://bud.embedlabs.de/"
export BUD_TOKEN="your-api-token"
export BLOOM_URL="https://bloom.embedlabs.de/"
export BLOOM_TOKEN="your-bloom-jwt-token"
export BLOOM_EMAIL="user@embedlabs.de"
export BLOOM_PASSWORD="your-password"
```

### app.properties

```properties
budBackend=https://bud.embedlabs.de/
budToken=your-api-token
bloomUrl=https://bloom.embedlabs.de/
bloomToken=your-bloom-jwt-token
bloomEmail=user@embedlabs.de
budRunnerAccount=my-runner
budRunnerToken=runner-token
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

## Bloom ALM Integration

Sync test cases to Bloom ALM:

```python
from budtestlibrary import BloomSync

sync = BloomSync()

# Sync a test suite
sync.sync_test_suite(
    project_identifier="bms-project",
    campaign_name="HIL Tests",
    test_classes=[MyBMSTest, AnotherTest],
)

# Update result after test run
sync.update_test_result(
    campaign_id=1,
    test_case_id=42,
    passed=True,
)
```

## JUnit XML Output

Generate JUnit XML for CI/CD integration:

```python
test = MyBMSTest()
test.run()

# Write JUnit XML
with open("report_junit.xml", "w") as f:
    f.write(test.to_junit_xml())
```

## Related Packages

- **bud_runner**: CLI tool for test execution and CI/CD integration
- **pybudgui**: PyQt6 desktop application for manual testing and result visualization

## License

This project is licensed under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**. See the [LICENSE](LICENSE) file for the full text.

Copyright (C) 2024-2026 EmbedLabs.

For commercial licensing options that do not require AGPL compliance, contact dev@embedlabs.de. Contributions are accepted under the [CLA](CLA.md) — see [CONTRIBUTING.md](CONTRIBUTING.md).
