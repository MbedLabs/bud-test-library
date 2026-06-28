# Changelog

All notable changes to `budtestlibrary` will be documented in this file.

## [1.0.0.post1] — 2026-06-28

### Changed
- Package version advanced to `1.0.0.post1` for a docs-only PyPI metadata correction
- Package author metadata now credits Amine El Omari
- README now credits the creator and marks the Qt desktop client as roadmap-only

## [1.0.0] — 2026-06-28

### Added
- Release metadata regression coverage for version, license metadata, and changelog alignment

### Changed
- Package version advanced to `1.0.0`
- Packaging metadata now uses a PEP 621-compatible license table
- Release classifier moved from beta to production/stable
- Runtime version resolution now prefers installed package metadata before falling back to local source metadata

## [0.3.0] — 2026-05-20

### Added
- New assertion methods: `assertFalse`, `assertNotEqual`, `assertGreater`, `assertLess`, `assertRegex`
- Configurable source path capture via `CAPTURE_SOURCE_PATH` class attribute
- Configurable traceback capture via `CAPTURE_TRACEBACK` class attribute
- `BloomMetaData` field validation (non-empty project/tc_id_suffix, alphanumeric suffix format)
- Result value truncation to prevent bloated reports (default max 5000 chars)

### Changed
- **Breaking**: `FlashFailure.message` is now a required positional argument (no longer defaults to "Flash failed")
- `BloomMetaData.get_url()` accepts a configurable `base_url` parameter
- `assertIn` / `assertNotIn` now raise `TypeError` for non-container arguments

### Fixed
- `assertInTolerance` with `absolute_tolerance=0` now correctly requires exact match (previously `0` was falsy and fell through to relative tolerance calculation)
- `BudTestCase` no longer mutates the root logger — uses its own `budtestlibrary.ClassName` logger with `propagate=False`
- Serialized result output (`to_dict()`) remains plain text — ANSI color codes only appear in console output

### Removed
- `FlashStatus` enum removed from `FlashResult`; use `is_success()` instead (status is derived, not stored)

## [0.2.0] — 2025

### Added
- Initial public release
- `BudTestCase` with lifecycle, assertions, and logging
- `BloomMetaData` for Bloom PLM integration
- `FlashEvent` abstraction for firmware flashing
- Environment variable and `app.properties` configuration
