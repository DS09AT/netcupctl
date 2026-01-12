"""Shared helper functions for CLI commands."""

import sys

import click


def get_authenticated_user_id(ctx) -> str:
    """Get the authenticated user's ID from token info.

    Args:
        ctx: Click context object with auth manager

    Returns:
        User ID string

    Exits:
        If not authenticated or user ID unavailable
    """
    info = ctx.auth.get_token_info()
    if not info or "user_id" not in info:
        click.echo("Error: Not authenticated. Run 'netcupctl auth login' first.", err=True)
        sys.exit(1)
    return info["user_id"]
