# Changelog

All notable changes to `budtestlibrary` will be documented in this file.

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
