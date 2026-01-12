"""Server management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.group()
def servers():
    """Server management commands.

    Manage your netcup vServers and root servers.

    \b
    Note: This command is also available as 'server'.
    """
    pass


@servers.command()
@click.option(
    "--limit",
    type=click.IntRange(min=0),
    default=100,
    help="Maximum number of servers to return (default: 100)",
)
@click.pass_obj
def list(ctx, limit: int):
    """List all servers.

    Displays a list of all servers associated with your account.
    """
    try:
        params = {"limit": limit}
        result = ctx.client.get("/api/v1/servers", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def get(ctx, server_id: str):
    """Get server details.

    \b
    Arguments:
        SERVER_ID: The ID of the server to retrieve
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def start(ctx, server_id: str):
    """Start a server.

    Powers on the server.

    \b
    Arguments:
        SERVER_ID: The ID of the server to start
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(f"/api/v1/servers/{server_id}", json={"state": "ON"})
        ctx.formatter.output(result)
        click.echo("\n[OK] Server start initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def stop(ctx, server_id: str):
    """Stop a server.

    Powers off the server (graceful shutdown via ACPI).

    \b
    Arguments:
        SERVER_ID: The ID of the server to stop
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(f"/api/v1/servers/{server_id}", json={"state": "OFF"})
        ctx.formatter.output(result)
        click.echo("\n[OK] Server stop initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def reboot(ctx, server_id: str):
    """Reboot a server.

    Performs a hard reset of the server.

    \b
    Arguments:
        SERVER_ID: The ID of the server to reboot
    """
    try:
        server_id = validate_server_id(server_id)
        params = {"stateOption": "RESET"}
        result = ctx.client.patch(f"/api/v1/servers/{server_id}", params=params, json={"state": "ON"})
        ctx.formatter.output(result)
        click.echo("\n[OK] Server reboot initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def poweroff(ctx, server_id: str):
    """Force power off a server.

    Immediately powers off the server without graceful shutdown (hard power off).
    This is equivalent to pulling the power cable.

    \b
    Arguments:
        SERVER_ID: The ID of the server to power off
    """
    try:
        server_id = validate_server_id(server_id)
        params = {"stateOption": "POWEROFF"}
        result = ctx.client.patch(f"/api/v1/servers/{server_id}", params=params, json={"state": "OFF"})
        ctx.formatter.output(result)
        click.echo("\n[OK] Server poweroff initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def status(ctx, server_id: str):
    """Get server status.

    Displays the current power state of the server.

    \b
    Arguments:
        SERVER_ID: The ID of the server

    \b
    Possible states:
        RUNNING      - Server is running
        SHUTOFF      - Server is powered off
        SHUTDOWN     - Server is shutting down
        BLOCKED      - Server is blocked
        PAUSED       - Server is paused
        CRASHED      - Server has crashed
        PMSUSPENDED  - Power management suspended
        DISK_SNAPSHOT - Disk snapshot in progress
        NOSTATE      - No state available
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}")

        state = result.get("serverLiveInfo", {}).get("state", "UNKNOWN")
        hostname = result.get("hostname", "")
        server_name = result.get("name", "")

        click.echo(f"Server: {hostname or server_name} (ID: {server_id})")
        click.echo(f"Status: {state}")
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
