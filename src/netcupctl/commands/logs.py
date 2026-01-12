"""Server logs command."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.command()
@click.argument("server_id")
@click.option(
    "--limit",
    type=int,
    default=50,
    help="Maximum number of log entries to return (default: 50)",
)
@click.option(
    "--offset",
    type=int,
    default=0,
    help="Number of entries to skip (default: 0)",
)
@click.pass_obj
def logs(ctx, server_id: str, limit: int, offset: int):
    """View server logs.

    Displays log entries for a server with pagination support.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        params = {"limit": limit, "offset": offset}
        result = ctx.client.get(f"/api/v1/servers/{server_id}/logs", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
