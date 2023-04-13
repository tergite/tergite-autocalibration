# Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project follows versions of format `{year}.{month}.{patch_number}`.

## [Unreleased]

### Added

- Added labels to the colorbar in the 2d plots.

### Bug Fixes
- Fixed bug where the colorbar levels were sometimes not being set correctly.

## [0.2.0] - 2023-04-12

### Added

- Added splitter to the plot window, allowing users to resize the left and right panels.
- Made the auto plot windows pop up as active windows on some operating systems.
- Added colorbar to the 2d plots.
- Added a warning on selecting an invalid data directory.
- Added a "Close all plots" action to the browser window under the "File" menu for convenience.

### Changed
- Migrated cli from click to typer
- Switch to quantify-scheduler version 0.21.2
- Switch to qblox-instruments version 0.14.1 (qblox-firmware should be 9.0.1)
- Upgrade to Python version 3.10

### Fixed

## [2024.09.0] - 2024-09-16

### Added
- superconducting_qubit_tools as conditional dependency
- Calibration node for purity benchmarking
- Redis storage manager
- GitLab CI/CD

### Changed
- Refactoring of the node classes to allow hierarchical class structures

### Fixed

## [2024.04.0] - 2024-05-29

This is part of the tergite release v2024.04 that updates the full pipeline for state discrimination hardware calibration

### Added
- All research-related features regarding the calibration of a CZ gate
- Updater to push calibration values as a backend to MSS/database

### Changed
- Improved command line interface
- Renamed from tergite-acl to tergite-autocalibration
- Updated the contribution guidelines and government model statements

### Fixed

## [2024.02.0] - 2024-03-19

This is part of the tergite release v2024.02 which introduces authentication, authorization and accounting to the
tergite stack.

No major change except for the versions.

### Added

### Changed

### Fixed

## [2023.12.0] - 2024-03-14

This is part of the tergite release v2023.12.0 that is the last to support [Labber](https://www.keysight.com/us/en/products/software/application-sw/labber-software.html).
Labber is being deprecated.

### Added

- Initial release of the automatic calibrator

### Changed

### Fixed

### Contributors

- Eleftherios Moschandreou
- Stefan Hill
- Liangyu Chen
- Tong Liu
- Martin Ahindura
- Michele Faucci Giannelli
