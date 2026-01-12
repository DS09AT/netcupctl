"""User management commands."""

import json
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.group()
def users():
    """User management commands.

    View and update user profile settings.
    """
    pass


@users.command("get")
@click.pass_obj
def get_user(ctx):
    """Get your user profile.

    Displays the profile information for the authenticated user.
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        result = ctx.client.get(f"/api/v1/users/{user_id}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@users.command("update")
@click.option("--data", required=True, help="User data as JSON string")
@click.pass_obj
def update_user(ctx, data: str):
    """Update your user profile.

    Provide user data as a JSON string.
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        user_data = json.loads(data)
        result = ctx.client.put(f"/api/v1/users/{user_id}", json=user_data)
        ctx.formatter.output(result)
        click.echo("\n[OK] User profile updated.", err=False)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {e}", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
