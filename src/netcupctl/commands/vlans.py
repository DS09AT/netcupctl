"""VLAN management commands."""

import json
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.group()
def vlans():
    """VLAN management commands.

    View and manage VLANs.
    """
    pass


@vlans.command("list")
@click.option("--server", help="Filter by server ID")
@click.pass_obj
def list_vlans(ctx, server: str):
    """List VLANs.

    Displays all VLANs, optionally filtered by server.
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        params = {}
        if server:
            params["serverId"] = server

        result = ctx.client.get(f"/api/v1/users/{user_id}/vlans", params=params or None)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@vlans.command("get")
@click.argument("vlan_id")
@click.pass_obj
def get_vlan(ctx, vlan_id: str):
    """Get details for a specific VLAN.

    \b
    Arguments:
        VLAN_ID: The ID of the VLAN
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        result = ctx.client.get(f"/api/v1/users/{user_id}/vlans/{vlan_id}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@vlans.command("info")
@click.argument("vlan_id")
@click.pass_obj
def info_vlan(ctx, vlan_id: str):
    """Get public VLAN information.

    Retrieves VLAN details without user context.
    Use 'vlans get' for user-specific VLAN details.

    \b
    Arguments:
        VLAN_ID: The ID of the VLAN
    """
    try:
        result = ctx.client.get(f"/api/v1/vlans/{vlan_id}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@vlans.command("update")
@click.argument("vlan_id")
@click.option("--name", help="New name for the VLAN")
@click.option("--data", help="VLAN data as JSON string")
@click.pass_obj
def update_vlan(ctx, vlan_id: str, name: str, data: str):
    """Update a VLAN.

    \b
    Arguments:
        VLAN_ID: The ID of the VLAN to update
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        vlan_data = {}

        if name:
            vlan_data["name"] = name

        if data:
            vlan_data.update(json.loads(data))

        if not vlan_data:
            raise click.UsageError("Provide at least one update option (--name, --data)")

        result = ctx.client.put(f"/api/v1/users/{user_id}/vlans/{vlan_id}", json=vlan_data)
        ctx.formatter.output(result)
        click.echo("\n[OK] VLAN updated.", err=False)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {e}", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
