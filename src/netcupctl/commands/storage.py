"""Storage optimization commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.group()
def storage():
    """Storage optimization commands.

    Manage storage optimization for your servers.
    """
    pass


@storage.command("show")
@click.argument("server_id")
@click.pass_obj
def show_storage(ctx, server_id: str):
    """Show storage optimization status for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/storageoptimization")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@storage.command("optimize")
@click.argument("server_id")
@click.option("--confirm", is_flag=True, help="Confirm the optimization")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def optimize_storage(ctx, server_id: str, confirm: bool, yes: bool):
    """Run storage optimization on a server.

    This may temporarily affect server performance.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)

        if not confirm and not yes:
            if not click.confirm("Run storage optimization? This may temporarily affect performance."):
                raise click.Abort()

        result = ctx.client.post(f"/api/v1/servers/{server_id}/storageoptimization")
        ctx.formatter.output(result)
        click.echo("\n[OK] Storage optimization started.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
