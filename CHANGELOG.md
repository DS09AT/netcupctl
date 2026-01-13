# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0](https://github.com/DS09AT/netcupctl/compare/v0.4.0...v0.5.0) (2026-01-13)


### Features

* Add verbose logging option to NetcupClient ([8919935](https://github.com/DS09AT/netcupctl/commit/8919935d4cc94e696e142805eca1e5278f4413f1))

## [0.4.0](https://github.com/DS09AT/netcupctl/compare/v0.3.1...v0.4.0) (2026-01-13)


### Features

* Add YAML output support to netcupctl ([c7c93e5](https://github.com/DS09AT/netcupctl/commit/c7c93e5e14643b8ee4cb4932bb57854d13c4e6d3))


### Documentation

* Improve help command usage examples in README ([d70436c](https://github.com/DS09AT/netcupctl/commit/d70436ce61e299d59bf1448dc4ddb973c3aed797))
* Update CHANGELOG with expanded feature list ([9ac0fee](https://github.com/DS09AT/netcupctl/commit/9ac0feec408395d39ccb45110d467f97e67100b5))

## [0.3.1](https://github.com/DS09AT/netcupctl/compare/v0.3.0...v0.3.1) (2026-01-12)


### Documentation

* Correct release date for version 0.1.0 ([2a8206f](https://github.com/DS09AT/netcupctl/commit/2a8206fc8e50e16ece334d66a9aff9d68a887ba6))

## [0.3.0](https://github.com/DS09AT/netcupctl/compare/v0.2.0...v0.3.0) (2026-01-12)


### Features

* Expand user update command options ([162ae7f](https://github.com/DS09AT/netcupctl/commit/162ae7f02155721c9f6e54b3a806384ab4130e22))


### Bug Fixes

* Include user ID in update payloads ([c7b23f5](https://github.com/DS09AT/netcupctl/commit/c7b23f53c8733c1d958dc143d13a795885db048c))
* Python 3.8 compatibility in output.py ([35ebbe0](https://github.com/DS09AT/netcupctl/commit/35ebbe01526bcefde5e8811bce451c4dea4e38a5))

## [0.2.0](https://github.com/DS09AT/netcupctl/compare/netcupctl-v0.1.0...netcupctl-v0.2.0) (2026-01-12)


### Features

* Add server status and poweroff commands, improve server state handling ([f6e6014](https://github.com/DS09AT/netcupctl/commit/f6e6014dfffa8fe432ed626fdef2b8a3e8f2aef4))

## [0.1.0] - 2026-01-12

### Added

- Initial release of netcupctl CLI tool
- Core CLI framework with Click
- OAuth2 device flow authentication
- Server Control Panel REST API client
- Server management commands (list, get, start, stop, reboot)
- Failover IP management commands (list, get, update)
- Reverse DNS (rDNS) management commands (get, set, delete)
- Disk management commands (list, get, format, set driver)
- Snapshot management commands (list, get, create, delete, revert, export, dry-run)
- Storage optimization commands
- Image management commands (list, show, install, custom images)
- ISO management commands (list, mount, unmount, custom ISOs)
- Network interface management (list, get, create, update, delete)
- VLAN management commands
- Firewall management (show, set, reapply, restore)
- Firewall policy management
- SSH key management
- User management and profile updates
- Guest agent control
- Rescue system management
- Task management and monitoring
- Server logs and metrics (CPU, disk, network)
- User activity logs
- Maintenance status checks
- OpenAPI specification download and management
- Rich console output formatting
- Multiple output formats (json, table, list)
- Multipart upload support for custom images and ISOs
- Comprehensive error handling and validation
- Strict linting configuration with pylint
- GitHub Actions workflow for PyPI publishing

### Documentation

- README with installation and usage instructions
- Command reference
- Output format examples
- Issue templates

[0.1.0]: https://github.com/DS09AT/netcupctl/releases/tag/v0.1.0
