# budtestlibrary

Test automation framework for embedded systems testing.

## Overview

`budtestlibrary` provides a comprehensive test framework for hardware-in-loop (HIL) and functional component testing (FCT) of embedded systems. It offers:

- **BudTestCase**: Base class for test cases with lifecycle management, rich assertions, and logging
- **RequirementMetadata**: Link tests to OpenProject/Jira for requirement traceability
- **FlashEvent**: Standardized firmware flashing abstraction
- **OpenProjectSync**: Automatic synchronization of test cases to OpenProject Work Packages

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
    # Link to OpenProject Work Package
    requirement_metadata = RequirementMetadata("bms-project", "WP-1234")
    
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
export PM_URL="https://pm.embedlabs.de/"
export PM_TOKEN="your-openproject-token"
```

### app.properties

```properties
budBackend=https://bud.embedlabs.de/
budToken=your-api-token
pmUrl=https://pm.embedlabs.de/
pmToken=your-openproject-token
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

## OpenProject Integration

Sync test cases to OpenProject Work Packages:

```python
from budtestlibrary import OpenProjectSync

sync = OpenProjectSync()

# Sync a test suite
sync.sync_test_suite(
    project_id="bms-project",
    suite_name="HIL Tests",
    test_classes=[MyBMSTest, AnotherTest],
)

# Update result after test run
sync.update_test_result(
    work_package_id=1234,
    passed=True,
    run_url="https://bud.embedlabs.de/runs/567",
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

MIT License - Copyright (c) 2025 EmbedLabs
