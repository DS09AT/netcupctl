"""Maintenance status command."""

import sys

import click

from netcupctl.client import APIError


@click.command()
@click.pass_obj
def maintenance(ctx):
    """Show API maintenance status.

    Displays current and scheduled maintenance information.
    """
    try:
        result = ctx.client.get("/api/v1/maintenance")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
