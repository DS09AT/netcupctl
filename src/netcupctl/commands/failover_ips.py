"""Failover IP management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.group(name="failover-ips")
def failover_ips():
    """Failover IP management commands.

    Manage failover IPs for high availability setups.
    """
    pass


@failover_ips.command("list")
@click.option("--version", "ip_version", type=click.Choice(["v4", "v6"]), help="Filter by IP version")
@click.pass_obj
def list_failover_ips(ctx, ip_version: str):
    """List all failover IPs.

    By default lists both IPv4 and IPv6 failover IPs.
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        results = []

        if ip_version is None or ip_version == "v4":
            results.extend(_fetch_failover_ips(ctx, user_id, "v4"))

        if ip_version is None or ip_version == "v6":
            results.extend(_fetch_failover_ips(ctx, user_id, "v6"))

        ctx.formatter.output(results)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


def _fetch_failover_ips(ctx, user_id: str, version: str):
    """Fetch failover IPs for a specific version.

    Args:
        ctx: Click context
        user_id: User ID
        version: IP version (v4 or v6)

    Returns:
        List of failover IPs with version tag
    """
    try:
        result = ctx.client.get(f"/api/v1/users/{user_id}/failoverips/{version}")
        return _normalize_failover_result(result, version)
    except APIError:
        return []


def _normalize_failover_result(result, version: str):
    """Normalize failover IP result to list format.

    Args:
        result: API response (dict or list)
        version: IP version tag to add

    Returns:
        List of failover IPs with version tag
    """
    if isinstance(result, list):
        for ip in result:
            ip["_version"] = version
        return result

    if result:
        result["_version"] = version
        return [result]

    return []


@failover_ips.command("get")
@click.argument("failover_id")
@click.option("--version", "ip_version", type=click.Choice(["v4", "v6"]), required=True, help="IP version (v4 or v6)")
@click.pass_obj
def get_failover_ip(ctx, failover_id: str, ip_version: str):
    """Get details for a specific failover IP.

    \b
    Arguments:
        FAILOVER_ID: The ID of the failover IP
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        result = ctx.client.get(f"/api/v1/users/{user_id}/failoverips/{ip_version}/{failover_id}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@failover_ips.command("update")
@click.argument("failover_id")
@click.option("--version", "ip_version", type=click.Choice(["v4", "v6"]), required=True, help="IP version (v4 or v6)")
@click.option("--server", "server_id", help="Target server ID")
@click.option("--mac", help="Target interface MAC address")
@click.pass_obj
def update_failover_ip(ctx, failover_id: str, ip_version: str, server_id: str, mac: str):
    """Update failover IP routing.

    Route the failover IP to a different server or interface.

    \b
    Arguments:
        FAILOVER_ID: The ID of the failover IP to update
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        update_data = {}

        if server_id:
            update_data["serverId"] = server_id

        if mac:
            update_data["mac"] = mac

        if not update_data:
            raise click.UsageError("Provide at least one update option (--server, --mac)")

        result = ctx.client.patch(f"/api/v1/users/{user_id}/failoverips/{ip_version}/{failover_id}", json=update_data)
        ctx.formatter.output(result)
        click.echo("\n[OK] Failover IP updated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
