"""Guest agent management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.group(name="guest-agent")
def guest_agent():
    """Guest agent management commands.

    Manage the QEMU guest agent on your servers.
    """
    pass


@guest_agent.command("show")
@click.argument("server_id")
@click.pass_obj
def show_guest_agent(ctx, server_id: str):
    """Show guest agent status for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/guest-agent")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@guest_agent.command("enable")
@click.argument("server_id")
@click.pass_obj
def enable_guest_agent(ctx, server_id: str):
    """Enable the guest agent on a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(f"/api/v1/servers/{server_id}/guest-agent", json={"enabled": True})
        ctx.formatter.output(result)
        click.echo("\n[OK] Guest agent enabled.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@guest_agent.command("disable")
@click.argument("server_id")
@click.pass_obj
def disable_guest_agent(ctx, server_id: str):
    """Disable the guest agent on a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(f"/api/v1/servers/{server_id}/guest-agent", json={"enabled": False})
        ctx.formatter.output(result)
        click.echo("\n[OK] Guest agent disabled.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
