# netcupctl

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

Manage your netcup vServers and root servers from the command line with automatic OAuth2 authentication and intuitive commands.

> **Disclaimer**: This is an unofficial, community-developed tool and is not affiliated with, endorsed by, or supported by netcup GmbH. Use at your own risk.

## Available Commands

**Authentication & Server Management**
- `netcupctl auth login | logout | status` - OAuth2 authentication
- `netcupctl servers list | get | start | stop | reboot <server-id>` - Server control
- `netcupctl ping` - API health check
- `netcupctl maintenance` - Maintenance status

**Storage & Snapshots**
- `netcupctl disks list | get | drivers | set-driver | format <server-id> [disk]` - Disk management
- `netcupctl snapshots list | get | create | delete | revert | export | dryrun <server-id> [name]` - Snapshot operations
- `netcupctl storage show | optimize <server-id>` - Storage optimization

**Network & Firewall**
- `netcupctl interfaces list | get | create | update | delete <server-id> [mac]` - Network interfaces
- `netcupctl vlans list | get | update <vlan-id>` - VLAN management
- `netcupctl rdns get | set | delete <server-id> <ip>` - Reverse DNS
- `netcupctl failover-ips list | get | update <id>` - Failover IP management
- `netcupctl firewall show | set | reapply | restore <server-id>` - Firewall rules
- `netcupctl firewall-policies list | get | create | update | delete [id]` - Firewall policies

**Monitoring & Logs**
- `netcupctl logs <server-id>` - Server logs
- `netcupctl metrics cpu | disk | network | network-packets <server-id>` - Resource metrics
- `netcupctl tasks list | get | cancel [task-id]` - Task management
- `netcupctl user-logs` - User activity logs

**Images & ISOs**
- `netcupctl images list | show | install | install-custom <server-id>` - OS image management
- `netcupctl custom-images list | get | upload | delete [key]` - Custom image upload
- `netcupctl iso images | show | mount | unmount <server-id>` - ISO mounting
- `netcupctl custom-isos list | get | upload | delete [key]` - Custom ISO upload

**Security & Access**
- `netcupctl ssh-keys list | add | delete [key-id]` - SSH key management
- `netcupctl rescue show | enable | disable <server-id>` - Rescue system
- `netcupctl guest-agent show | enable | disable <server-id>` - Guest agent control
- `netcupctl users get | update` - User profile management

**Utilities**
- `netcupctl spec update | show` - OpenAPI specification management

Use `netcupctl <command> --help` to see all available options and flags.

## Installation

### Requirements

- Python 3.8 or higher
- A netcup customer account with vServer or root server products

### Install

```bash
# From PyPI
pip install netcupctl

# Or from source
git clone https://github.com/DS09AT/netcupctl.git
cd netcupctl
pip install .
```

## Quick Start

### 1. Login

First, authenticate with your netcup account:

```bash
netcupctl auth login
```

This will open your browser for authentication. After successful login, tokens are stored locally.

### 2. List Your Servers

```bash
netcupctl servers list
```

### 3. Get Server Details

```bash
netcupctl servers get <server-id>
```

### 4. Manage Server State

```bash
# Start a server
netcupctl servers start <server-id>

# Stop a server
netcupctl servers stop <server-id>

# Reboot a server
netcupctl servers reboot <server-id>
```

## Output Formats

Use `--format` to control output. Default is `list`.

```bash
# List format (default) - human-readable key-value
netcupctl servers list

# Table format - columnar layout
netcupctl --format table servers list

# JSON format - for scripting
netcupctl --format json servers list | jq '.[] | .hostname'
```

## API Documentation

- [API Browser](https://www.netcup.com/en/helpcenter/documentation/servercontrolpanel/api)
- [OpenAPI Specification](https://servercontrolpanel.de/scp-core/api/v1/openapi)
- [netcup SCP REST API Forum](https://forum.netcup.de/netcup-anwendungen/scp-server-control-panel/scp-server-control-panel-rest-api/)

## License

MIT License. See [LICENSE.md](LICENSE.md) for details.
