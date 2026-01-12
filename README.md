# netcupctl

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

CLI client for the netcup Server Control Panel REST API.

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
