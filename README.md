# netcupctl

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

Manage your netcup vServers and root servers from the command line with automatic OAuth2 authentication and intuitive commands.

> **Disclaimer**: This is an unofficial, community-developed tool and is not affiliated with, endorsed by, or supported by netcup GmbH. Use at your own risk.

## Available Commands

### Authentication

| Command | Description |
|---------|-------------|
| `netcupctl auth login` | Login using OAuth2 |
| `netcupctl auth logout` | Logout and revoke tokens |
| `netcupctl auth status` | Show authentication status |

### Server Management

| Command | Description |
|---------|-------------|
| `netcupctl servers list` | List all servers |
| `netcupctl servers get <id>` | Get server details |
| `netcupctl servers start <id>` | Start a server |
| `netcupctl servers stop <id>` | Stop a server |
| `netcupctl servers reboot <id>` | Reboot a server |

### Disk Management

| Command | Description |
|---------|-------------|
| `netcupctl disks list <server-id>` | List all disks |
| `netcupctl disks get <server-id> <disk>` | Get disk details |
| `netcupctl disks drivers <server-id>` | List supported drivers |
| `netcupctl disks set-driver <server-id> --driver <name>` | Change disk driver |
| `netcupctl disks format <server-id> <disk> --confirm` | Format a disk |

### Snapshot Management

| Command | Description |
|---------|-------------|
| `netcupctl snapshots list <server-id>` | List all snapshots |
| `netcupctl snapshots get <server-id> <name>` | Get snapshot details |
| `netcupctl snapshots create <server-id> --name <name>` | Create a snapshot |
| `netcupctl snapshots delete <server-id> <name> --confirm` | Delete a snapshot |
| `netcupctl snapshots revert <server-id> <name> --confirm` | Revert to snapshot |
| `netcupctl snapshots export <server-id> <name>` | Export a snapshot |
| `netcupctl snapshots dryrun <server-id> --name <name>` | Test snapshot creation |

### Network Interfaces

| Command | Description |
|---------|-------------|
| `netcupctl interfaces list <server-id>` | List all interfaces |
| `netcupctl interfaces get <server-id> <mac>` | Get interface details |
| `netcupctl interfaces create <server-id>` | Create an interface |
| `netcupctl interfaces update <server-id> <mac>` | Update an interface |
| `netcupctl interfaces delete <server-id> <mac> --confirm` | Delete an interface |

### Monitoring

| Command | Description |
|---------|-------------|
| `netcupctl logs <server-id>` | View server logs |
| `netcupctl metrics cpu <server-id>` | View CPU metrics |
| `netcupctl metrics disk <server-id>` | View disk metrics |
| `netcupctl metrics network <server-id>` | View network metrics |
| `netcupctl metrics network-packets <server-id>` | View network packet metrics |

### Rescue System

| Command | Description |
|---------|-------------|
| `netcupctl rescue show <server-id>` | Show rescue status |
| `netcupctl rescue enable <server-id>` | Enable rescue mode |
| `netcupctl rescue disable <server-id>` | Disable rescue mode |

### ISO Management

| Command | Description |
|---------|-------------|
| `netcupctl iso images <server-id>` | List available ISOs |
| `netcupctl iso show <server-id>` | Show mounted ISO |
| `netcupctl iso mount <server-id> <iso>` | Mount an ISO |
| `netcupctl iso unmount <server-id>` | Unmount ISO |

### rDNS Management

| Command | Description |
|---------|-------------|
| `netcupctl rdns get <server-id> <ip>` | Get rDNS record |
| `netcupctl rdns set <server-id> <ip> --hostname <name>` | Set rDNS hostname |
| `netcupctl rdns delete <server-id> <ip>` | Delete rDNS record |

### Task Management

| Command | Description |
|---------|-------------|
| `netcupctl tasks list` | List all tasks |
| `netcupctl tasks get <task-id>` | Get task details |
| `netcupctl tasks cancel <task-id>` | Cancel a task |

### Server Firewall

| Command | Description |
|---------|-------------|
| `netcupctl firewall show <server-id>` | Show firewall config |
| `netcupctl firewall set <server-id> --policy <id>` | Set firewall policy |
| `netcupctl firewall reapply <server-id>` | Reapply firewall rules |
| `netcupctl firewall restore <server-id>` | Restore default firewall |

### Firewall Policies

| Command | Description |
|---------|-------------|
| `netcupctl firewall-policies list` | List all policies |
| `netcupctl firewall-policies get <id>` | Get policy details |
| `netcupctl firewall-policies create --name <name>` | Create a policy |
| `netcupctl firewall-policies update <id>` | Update a policy |
| `netcupctl firewall-policies delete <id> --confirm` | Delete a policy |

### User Management

| Command | Description |
|---------|-------------|
| `netcupctl users get` | Get your user profile |
| `netcupctl users update --data <json>` | Update your profile |

### VLAN Management

| Command | Description |
|---------|-------------|
| `netcupctl vlans list` | List all VLANs |
| `netcupctl vlans get <vlan-id>` | Get VLAN details |
| `netcupctl vlans update <vlan-id>` | Update a VLAN |

### SSH Key Management

| Command | Description |
|---------|-------------|
| `netcupctl ssh-keys list` | List all SSH keys |
| `netcupctl ssh-keys add --name <name> --key <key>` | Add an SSH key |
| `netcupctl ssh-keys delete <key-id> --confirm` | Delete an SSH key |

### Server Images

| Command | Description |
|---------|-------------|
| `netcupctl images list <server-id>` | List available OS images |
| `netcupctl images show <server-id>` | Show installed image |
| `netcupctl images install <server-id> --flavour <id>` | Install OS image |
| `netcupctl images install-custom <server-id> --image <key>` | Install custom image |

### Failover IPs

| Command | Description |
|---------|-------------|
| `netcupctl failover-ips list` | List all failover IPs |
| `netcupctl failover-ips get <id> --version <v4\|v6>` | Get failover IP details |
| `netcupctl failover-ips update <id> --version <v4\|v6>` | Update failover IP routing |

### Guest Agent

| Command | Description |
|---------|-------------|
| `netcupctl guest-agent show <server-id>` | Show guest agent status |
| `netcupctl guest-agent enable <server-id>` | Enable guest agent |
| `netcupctl guest-agent disable <server-id>` | Disable guest agent |

### Storage Optimization

| Command | Description |
|---------|-------------|
| `netcupctl storage show <server-id>` | Show storage status |
| `netcupctl storage optimize <server-id>` | Run optimization |

### Custom Images

| Command | Description |
|---------|-------------|
| `netcupctl custom-images list` | List custom images |
| `netcupctl custom-images get <key>` | Get image details |
| `netcupctl custom-images upload <file>` | Upload custom image |
| `netcupctl custom-images delete <key> --confirm` | Delete custom image |

### Custom ISOs

| Command | Description |
|---------|-------------|
| `netcupctl custom-isos list` | List custom ISOs |
| `netcupctl custom-isos get <key>` | Get ISO details |
| `netcupctl custom-isos upload <file>` | Upload custom ISO |
| `netcupctl custom-isos delete <key> --confirm` | Delete custom ISO |

### Utility Commands

| Command | Description |
|---------|-------------|
| `netcupctl ping` | Check API availability |
| `netcupctl maintenance` | Show maintenance status |
| `netcupctl user-logs` | View user activity logs |

### OpenAPI Specification

| Command | Description |
|---------|-------------|
| `netcupctl spec update` | Download/update OpenAPI spec |
| `netcupctl spec show` | Show current spec version |

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

### JSON

```bash
netcupctl servers list
```

```json
{
  "servers": [
    {
      "id": "abc123",
      "hostname": "server1.example.com",
      "state": "running"
    }
  ]
}
```

### Table

```bash
netcupctl --format table servers list
```

```
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ id     ┃ hostname               ┃ state   ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ abc123 │ server1.example.com    │ running │
└────────┴────────────────────────┴─────────┘
```

## API Documentation

- [API Browser](https://www.netcup.com/en/helpcenter/documentation/servercontrolpanel/api)
- [OpenAPI Specification](https://servercontrolpanel.de/scp-core/api/v1/openapi)
- [netcup SCP REST API Forum](https://forum.netcup.de/netcup-anwendungen/scp-server-control-panel/scp-server-control-panel-rest-api/)

## License

MIT License. See [LICENSE.md](LICENSE.md) for details.
