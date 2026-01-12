# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0](https://github.com/DS09AT/netcupctl/compare/v0.2.0...v0.3.0) (2026-01-12)


### Features

* Expand user update command options ([162ae7f](https://github.com/DS09AT/netcupctl/commit/162ae7f02155721c9f6e54b3a806384ab4130e22))


### Bug Fixes

* Include user ID in update payloads ([c7b23f5](https://github.com/DS09AT/netcupctl/commit/c7b23f53c8733c1d958dc143d13a795885db048c))
* Python 3.8 compatibility in output.py ([35ebbe0](https://github.com/DS09AT/netcupctl/commit/35ebbe01526bcefde5e8811bce451c4dea4e38a5))

## [0.2.0](https://github.com/DS09AT/netcupctl/compare/netcupctl-v0.1.0...netcupctl-v0.2.0) (2026-01-12)


### Features

* Add server status and poweroff commands, improve server state handling ([f6e6014](https://github.com/DS09AT/netcupctl/commit/f6e6014dfffa8fe432ed626fdef2b8a3e8f2aef4))

## [0.1.0] - 2025-01-12

### Added

- Initial release of netcupctl CLI tool
- Core CLI framework with Click
- Server Control Panel REST API client
- Server management commands (list, get, start, stop, restart, reset)
- Failover IP management commands
- Reverse DNS (rDNS) management commands
- Resource management commands (storage, snapshots, images)
- OpenAPI specification download and management
- Rich console output formatting
- Multiple output formats (json, yaml, table, list)
- Comprehensive error handling
- Strict linting configuration with pylint
- GitHub Actions workflow for PyPI publishing

### Documentation

- README with installation and usage instructions
- API endpoint documentation
- Command reference
- Configuration guide

[0.1.0]: https://github.com/DS09AT/netcupctl/releases/tag/v0.1.0
