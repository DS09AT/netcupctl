"""ISO management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.group()
def iso():
    """ISO image management commands.

    Mount and unmount ISO images on your servers.
    """
    pass


@iso.command("images")
@click.argument("server_id")
@click.pass_obj
def list_images(ctx, server_id: str):
    """List available ISO images.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/isoimages")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@iso.command("show")
@click.argument("server_id")
@click.pass_obj
def show_iso(ctx, server_id: str):
    """Show currently mounted ISO.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/iso")
        if result:
            ctx.formatter.output(result)
        else:
            click.echo("No ISO mounted.")
    except APIError as e:
        if e.status_code == 404:
            click.echo("No ISO mounted.")
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(e.status_code or 1)


@iso.command("mount")
@click.argument("server_id")
@click.argument("iso_name")
@click.pass_obj
def mount_iso(ctx, server_id: str, iso_name: str):
    """Mount an ISO image.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        ISO_NAME: The name of the ISO image to mount
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.post(
            f"/api/v1/servers/{server_id}/iso", json={"isoImage": iso_name}
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] ISO mounted.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@iso.command("unmount")
@click.argument("server_id")
@click.pass_obj
def unmount_iso(ctx, server_id: str):
    """Unmount the currently mounted ISO.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.delete(f"/api/v1/servers/{server_id}/iso")
        ctx.formatter.output(result)
        click.echo("\n[OK] ISO unmounted.", err=False)
    except APIError as e:
        if e.status_code == 404:
            click.echo("No ISO was mounted.")
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(e.status_code or 1)
