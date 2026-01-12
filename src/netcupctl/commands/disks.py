"""Disk management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_disk_name, validate_server_id


@click.group()
def disks():
    """Disk management commands.

    Manage disks attached to your servers.
    """
    pass


@disks.command("list")
@click.argument("server_id")
@click.pass_obj
def list_disks(ctx, server_id: str):
    """List all disks for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/disks")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@disks.command("get")
@click.argument("server_id")
@click.argument("disk_name")
@click.pass_obj
def get_disk(ctx, server_id: str, disk_name: str):
    """Get details for a specific disk.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        DISK_NAME: The name of the disk
    """
    try:
        server_id = validate_server_id(server_id)
        disk_name = validate_disk_name(disk_name)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/disks/{disk_name}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@disks.command("drivers")
@click.argument("server_id")
@click.pass_obj
def list_drivers(ctx, server_id: str):
    """List supported disk drivers for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/disks/supported-drivers")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@disks.command("set-driver")
@click.argument("server_id")
@click.option("--driver", required=True, help="The disk driver to use")
@click.pass_obj
def set_driver(ctx, server_id: str, driver: str):
    """Change the disk driver for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.patch(
            f"/api/v1/servers/{server_id}/disks", json={"driver": driver}
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Disk driver updated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@disks.command("format")
@click.argument("server_id")
@click.argument("disk_name")
@click.option("--confirm", is_flag=True, help="Confirm the format operation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def format_disk(ctx, server_id: str, disk_name: str, confirm: bool, yes: bool):
    """Format a disk (DESTRUCTIVE).

    WARNING: This will destroy all data on the disk!

    \b
    Arguments:
        SERVER_ID: The ID of the server
        DISK_NAME: The name of the disk to format
    """
    try:
        server_id = validate_server_id(server_id)
        disk_name = validate_disk_name(disk_name)

        if not confirm and not yes:
            if not click.confirm(
                f"Format disk '{disk_name}'? This will DESTROY ALL DATA!"
            ):
                raise click.Abort()

        result = ctx.client.post(f"/api/v1/servers/{server_id}/disks/{disk_name}:format")
        ctx.formatter.output(result)
        click.echo("\n[OK] Disk format initiated.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
