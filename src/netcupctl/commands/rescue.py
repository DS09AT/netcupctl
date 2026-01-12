"""Rescue system commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.group()
def rescue():
    """Rescue system commands.

    Enable or disable the rescue system for troubleshooting.
    """
    pass


@rescue.command("show")
@click.argument("server_id")
@click.pass_obj
def show_rescue(ctx, server_id: str):
    """Show rescue system status.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/rescuesystem")
        ctx.formatter.output(result)
    except APIError as e:
        if e.status_code == 404:
            click.echo("Rescue system is not active.")
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(e.status_code or 1)


@rescue.command("enable")
@click.argument("server_id")
@click.option("--os", "os_type", default="linux", help="Rescue OS type (default: linux)")
@click.pass_obj
def enable_rescue(ctx, server_id: str, os_type: str):
    """Enable rescue mode.

    After enabling, reboot the server to boot into rescue mode.
    The rescue system credentials will be displayed.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.post(
            f"/api/v1/servers/{server_id}/rescuesystem", json={"os": os_type}
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Rescue mode enabled.", err=False)
        click.echo("Reboot the server to boot into rescue mode.", err=False)
        click.echo("\nWARNING: Rescue credentials are temporary. Change password after login.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@rescue.command("disable")
@click.argument("server_id")
@click.pass_obj
def disable_rescue(ctx, server_id: str):
    """Disable rescue mode.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.delete(f"/api/v1/servers/{server_id}/rescuesystem")
        ctx.formatter.output(result)
        click.echo("\n[OK] Rescue mode disabled.", err=False)
    except APIError as e:
        if e.status_code == 404:
            click.echo("Rescue mode was not active.")
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(e.status_code or 1)
