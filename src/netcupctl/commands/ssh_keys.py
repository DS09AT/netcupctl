"""SSH key management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.group(name="ssh-keys")
def ssh_keys():
    """SSH key management commands.

    Manage SSH keys for your account.
    """
    pass


@ssh_keys.command("list")
@click.pass_obj
def list_keys(ctx):
    """List all SSH keys."""
    try:
        user_id = get_authenticated_user_id(ctx)
        result = ctx.client.get(f"/api/v1/users/{user_id}/ssh-keys")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@ssh_keys.command("add")
@click.option("--name", required=True, help="Name for the SSH key")
@click.option("--key", help="Public SSH key string")
@click.option("--key-file", type=click.File("r"), help="Read public key from file")
@click.pass_obj
def add_key(ctx, name: str, key: str, key_file):
    """Add a new SSH key.

    Provide the public key as a string or from a file.
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        if key_file:
            public_key = key_file.read().strip()
        elif key:
            public_key = key.strip()
        else:
            raise click.UsageError("Provide --key or --key-file")

        key_data = {"name": name, "key": public_key}
        result = ctx.client.post(f"/api/v1/users/{user_id}/ssh-keys", json=key_data)
        ctx.formatter.output(result)
        click.echo("\n[OK] SSH key added.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@ssh_keys.command("delete")
@click.argument("key_id")
@click.option("--confirm", is_flag=True, help="Confirm the delete operation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def delete_key(ctx, key_id: str, confirm: bool, yes: bool):
    """Delete an SSH key.

    \b
    Arguments:
        KEY_ID: The ID of the SSH key to delete
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        if not confirm and not yes:
            if not click.confirm(f"Delete SSH key '{key_id}'? This cannot be undone."):
                raise click.Abort()

        result = ctx.client.delete(f"/api/v1/users/{user_id}/ssh-keys/{key_id}")
        ctx.formatter.output(result)
        click.echo("\n[OK] SSH key deleted.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
