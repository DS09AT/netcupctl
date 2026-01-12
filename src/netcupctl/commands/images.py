"""Server image management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.group()
def images():
    """Server image management commands.

    Manage OS images and installations on your servers.
    """
    pass


@images.command("list")
@click.argument("server_id")
@click.pass_obj
def list_flavours(ctx, server_id: str):
    """List available image flavours for a server.

    Shows all OS images that can be installed on the server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/imageflavours")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@images.command("show")
@click.argument("server_id")
@click.pass_obj
def show_image(ctx, server_id: str):
    """Show currently installed image on a server.

    Displays details about the OS image currently installed.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/image")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@images.command("install")
@click.argument("server_id")
@click.option("--flavour", required=True, help="Image flavour ID to install")
@click.option("--hostname", help="Hostname for the server")
@click.option("--password", help="Root password (will be prompted if not provided)")
@click.option("--ssh-keys", help="Comma-separated SSH key IDs")
@click.option("--confirm", is_flag=True, help="Confirm the installation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def install_image(
    ctx, server_id: str, flavour: str, hostname: str,
    password: str, ssh_keys: str, confirm: bool, yes: bool
):
    """Install an OS image on a server.

    WARNING: This will OVERWRITE ALL DATA on the server!

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)

        if not confirm and not yes:
            click.echo("WARNING: This will OVERWRITE ALL DATA on the server!", err=True)
            if not click.confirm("Are you sure you want to continue?"):
                raise click.Abort()

        if not password:
            password = click.prompt("Root password", hide_input=True, confirmation_prompt=True)

        image_data = {"imageFlavourId": flavour}

        if hostname:
            image_data["hostname"] = hostname

        if password:
            image_data["password"] = password

        if ssh_keys:
            image_data["sshKeyIds"] = [k.strip() for k in ssh_keys.split(",")]

        result = ctx.client.post(f"/api/v1/servers/{server_id}/image", json=image_data)
        ctx.formatter.output(result)
        click.echo("\n[OK] Image installation started. Use 'netcupctl tasks list' to monitor progress.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@images.command("install-custom")
@click.argument("server_id")
@click.option("--image", "image_key", required=True, help="Custom image key")
@click.option("--confirm", is_flag=True, help="Confirm the installation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def install_custom_image(ctx, server_id: str, image_key: str, confirm: bool, yes: bool):
    """Install a custom user image on a server.

    WARNING: This will OVERWRITE ALL DATA on the server!

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)

        if not confirm and not yes:
            click.echo("WARNING: This will OVERWRITE ALL DATA on the server!", err=True)
            if not click.confirm("Are you sure you want to continue?"):
                raise click.Abort()

        image_data = {"key": image_key}
        result = ctx.client.post(f"/api/v1/servers/{server_id}/user-image", json=image_data)
        ctx.formatter.output(result)
        msg = "[OK] Custom image installation started. Use 'netcupctl tasks list' to monitor."
        click.echo(f"\n{msg}", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
