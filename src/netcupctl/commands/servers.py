"""Server management commands."""

import re
import sys

import click

from netcupctl.client import APIError


def validate_server_id(server_id: str) -> str:
    """Validate server ID to prevent injection attacks.

    Args:
        server_id: Server ID to validate

    Returns:
        Validated server ID

    Raises:
        click.BadParameter: If server ID is invalid
    """
    if not re.match(r'^[a-zA-Z0-9_-]+$', server_id):
        raise click.BadParameter("Server ID contains invalid characters")
    if len(server_id) > 64:
        raise click.BadParameter("Server ID is too long")
    return server_id


@click.group()
def servers():
    """Server management commands.

    Manage your netcup vServers and root servers.
    """
    pass


@servers.command()
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of servers to return (default: 100)",
)
@click.pass_obj
def list(ctx, limit: int):
    """List all servers.

    Displays a list of all servers associated with your account.
    """
    try:
        params = {"limit": limit} if limit else None
        result = ctx.client.get("/api/v1/servers", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


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
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def start(ctx, server_id: str):
    """Start a server.

    Changes the server state to 'running'.

    \b
    Arguments:
        SERVER_ID: The ID of the server to start
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(f"/api/v1/servers/{server_id}", json={"state": "running"})
        ctx.formatter.output(result)
        click.echo("\n[OK] Server start initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def stop(ctx, server_id: str):
    """Stop a server.

    Changes the server state to 'stopped' (graceful shutdown).

    \b
    Arguments:
        SERVER_ID: The ID of the server to stop
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(f"/api/v1/servers/{server_id}", json={"state": "stopped"})
        ctx.formatter.output(result)
        click.echo("\n[OK] Server stop initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@servers.command()
@click.argument("server_id")
@click.pass_obj
def reboot(ctx, server_id: str):
    """Reboot a server.

    Performs a graceful reboot of the server.

    \b
    Arguments:
        SERVER_ID: The ID of the server to reboot
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(f"/api/v1/servers/{server_id}", json={"state": "reboot"})
        ctx.formatter.output(result)
        click.echo("\n[OK] Server reboot initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
