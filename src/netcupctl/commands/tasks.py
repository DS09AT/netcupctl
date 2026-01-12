"""Task management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_uuid


@click.group()
def tasks():
    """Task management commands.

    Monitor and manage background tasks.
    """
    pass


@tasks.command("list")
@click.option("--state", help="Filter by task state (e.g., running, completed, failed)")
@click.option("--server", help="Filter by server ID")
@click.option("--search", "-q", help="Search query")
@click.option("--limit", type=int, default=50, help="Maximum number of tasks (default: 50)")
@click.option("--offset", type=int, default=0, help="Number of tasks to skip (default: 0)")
@click.pass_obj
def list_tasks(ctx, state: str, server: str, search: str, limit: int, offset: int):
    """List background tasks.

    Displays tasks with optional filtering by state, server, or search query.
    """
    try:
        params = {"limit": limit, "offset": offset}
        if state:
            params["state"] = state
        if server:
            params["serverId"] = server
        if search:
            params["q"] = search

        result = ctx.client.get("/api/v1/tasks", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@tasks.command("get")
@click.argument("uuid")
@click.pass_obj
def get_task(ctx, uuid: str):
    """Get details for a specific task.

    \b
    Arguments:
        UUID: The task UUID
    """
    try:
        uuid = validate_uuid(uuid)
        result = ctx.client.get(f"/api/v1/tasks/{uuid}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@tasks.command("cancel")
@click.argument("uuid")
@click.pass_obj
def cancel_task(ctx, uuid: str):
    """Cancel a running task.

    \b
    Arguments:
        UUID: The task UUID to cancel
    """
    try:
        uuid = validate_uuid(uuid)
        result = ctx.client.put(f"/api/v1/tasks/{uuid}:cancel")
        ctx.formatter.output(result)
        click.echo("\n[OK] Task cancellation requested.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
