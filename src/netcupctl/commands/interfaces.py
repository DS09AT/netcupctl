"""Network interface management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_mac_address, validate_server_id


@click.group()
def interfaces():
    """Network interface management commands.

    Manage network interfaces attached to your servers.
    """
    pass


@interfaces.command("list")
@click.argument("server_id")
@click.pass_obj
def list_interfaces(ctx, server_id: str):
    """List all network interfaces for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/interfaces")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@interfaces.command("get")
@click.argument("server_id")
@click.argument("mac")
@click.pass_obj
def get_interface(ctx, server_id: str, mac: str):
    """Get details for a specific network interface.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        MAC: The MAC address of the interface (XX:XX:XX:XX:XX:XX)
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/interfaces/{mac}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@interfaces.command("create")
@click.argument("server_id")
@click.option("--vlan", type=int, help="VLAN ID to attach the interface to")
@click.pass_obj
def create_interface(ctx, server_id: str, vlan: int):
    """Create a new network interface.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        json_data = {}
        if vlan is not None:
            json_data["vlanId"] = vlan

        result = ctx.client.post(
            f"/api/v1/servers/{server_id}/interfaces", json=json_data or None
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Interface created.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@interfaces.command("update")
@click.argument("server_id")
@click.argument("mac")
@click.option("--vlan", type=int, help="VLAN ID to attach the interface to")
@click.pass_obj
def update_interface(ctx, server_id: str, mac: str, vlan: int):
    """Update a network interface.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        MAC: The MAC address of the interface (XX:XX:XX:XX:XX:XX)
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)
        json_data = {}
        if vlan is not None:
            json_data["vlanId"] = vlan

        if not json_data:
            click.echo("Error: No update options provided.", err=True)
            sys.exit(1)

        result = ctx.client.put(
            f"/api/v1/servers/{server_id}/interfaces/{mac}", json=json_data
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Interface updated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@interfaces.command("delete")
@click.argument("server_id")
@click.argument("mac")
@click.option("--confirm", is_flag=True, help="Confirm the delete operation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def delete_interface(ctx, server_id: str, mac: str, confirm: bool, yes: bool):
    """Delete a network interface.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        MAC: The MAC address of the interface to delete
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)

        if not confirm and not yes:
            if not click.confirm(f"Delete interface '{mac}'? This cannot be undone."):
                raise click.Abort()

        result = ctx.client.delete(f"/api/v1/servers/{server_id}/interfaces/{mac}")
        ctx.formatter.output(result)
        click.echo("\n[OK] Interface deleted.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
