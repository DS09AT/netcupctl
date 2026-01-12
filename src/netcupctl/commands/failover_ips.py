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
            try:
                v4_result = ctx.client.get(f"/api/v1/users/{user_id}/failoverips/v4")
                if isinstance(v4_result, list):
                    for ip in v4_result:
                        ip["_version"] = "v4"
                    results.extend(v4_result)
                elif v4_result:
                    v4_result["_version"] = "v4"
                    results.append(v4_result)
            except APIError:
                pass  # No v4 failover IPs

        if ip_version is None or ip_version == "v6":
            try:
                v6_result = ctx.client.get(f"/api/v1/users/{user_id}/failoverips/v6")
                if isinstance(v6_result, list):
                    for ip in v6_result:
                        ip["_version"] = "v6"
                    results.extend(v6_result)
                elif v6_result:
                    v6_result["_version"] = "v6"
                    results.append(v6_result)
            except APIError:
                pass  # No v6 failover IPs

        ctx.formatter.output(results)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


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
