"""User logs command."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.command(name="user-logs")
@click.option("--limit", type=int, default=50, help="Maximum number of entries (default: 50)")
@click.option("--offset", type=int, default=0, help="Number of entries to skip (default: 0)")
@click.pass_obj
def user_logs(ctx, limit: int, offset: int):
    """View user activity logs.

    Shows activity logs for the authenticated user account.
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        params = {"limit": limit, "offset": offset}
        result = ctx.client.get(f"/api/v1/users/{user_id}/logs", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
