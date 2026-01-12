"""Shared validation functions for CLI commands."""

import ipaddress
import re
import uuid as uuid_module
from typing import Tuple

import click


def validate_server_id(server_id: str) -> str:
    """Validate server ID to prevent injection attacks.

    Args:
        server_id: Server ID to validate

    Returns:
        Validated server ID

    Raises:
        click.BadParameter: If server ID is invalid
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", server_id):
        raise click.BadParameter("Server ID contains invalid characters")
    if len(server_id) > 64:
        raise click.BadParameter("Server ID is too long")
    return server_id


def validate_mac_address(mac: str) -> str:
    """Validate MAC address format.

    Args:
        mac: MAC address to validate

    Returns:
        Validated MAC address (lowercase)

    Raises:
        click.BadParameter: If MAC address format is invalid
    """
    if not re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", mac):
        raise click.BadParameter("Invalid MAC address format (expected XX:XX:XX:XX:XX:XX)")
    return mac.lower()


def validate_snapshot_name(name: str) -> str:
    """Validate snapshot name format.

    Args:
        name: Snapshot name to validate

    Returns:
        Validated snapshot name

    Raises:
        click.BadParameter: If snapshot name is invalid
    """
    if not name or not name.strip():
        raise click.BadParameter("Snapshot name cannot be empty")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
        raise click.BadParameter("Snapshot name contains invalid characters")
    if len(name) > 128:
        raise click.BadParameter("Snapshot name is too long (max 128 characters)")
    return name


def validate_disk_name(name: str) -> str:
    """Validate disk name format.

    Args:
        name: Disk name to validate

    Returns:
        Validated disk name

    Raises:
        click.BadParameter: If disk name is invalid
    """
    if not name or not name.strip():
        raise click.BadParameter("Disk name cannot be empty")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
        raise click.BadParameter("Disk name contains invalid characters")
    if len(name) > 64:
        raise click.BadParameter("Disk name is too long (max 64 characters)")
    return name


def validate_ipv4(ip: str) -> str:
    """Validate IPv4 address format.

    Args:
        ip: IPv4 address to validate

    Returns:
        Validated IPv4 address

    Raises:
        click.BadParameter: If IP address format is invalid
    """
    try:
        addr = ipaddress.IPv4Address(ip)
        return str(addr)
    except ipaddress.AddressValueError:
        raise click.BadParameter("Invalid IPv4 address format")


def validate_ipv6(ip: str) -> str:
    """Validate IPv6 address format.

    Args:
        ip: IPv6 address to validate

    Returns:
        Validated IPv6 address

    Raises:
        click.BadParameter: If IP address format is invalid
    """
    try:
        addr = ipaddress.IPv6Address(ip)
        return str(addr)
    except ipaddress.AddressValueError:
        raise click.BadParameter("Invalid IPv6 address format")


def validate_ip(ip: str) -> Tuple[str, str]:
    """Validate IP address and detect version.

    Args:
        ip: IP address to validate (IPv4 or IPv6)

    Returns:
        Tuple of (validated IP, version string "v4" or "v6")

    Raises:
        click.BadParameter: If IP address format is invalid
    """
    try:
        addr = ipaddress.ip_address(ip)
        if isinstance(addr, ipaddress.IPv4Address):
            return str(addr), "v4"
        else:
            return str(addr), "v6"
    except ValueError:
        raise click.BadParameter("Invalid IP address format")


def validate_uuid(value: str) -> str:
    """Validate UUID format.

    Args:
        value: UUID string to validate

    Returns:
        Validated UUID string

    Raises:
        click.BadParameter: If UUID format is invalid
    """
    try:
        uuid_module.UUID(value)
        return value
    except ValueError:
        raise click.BadParameter("Invalid UUID format")
