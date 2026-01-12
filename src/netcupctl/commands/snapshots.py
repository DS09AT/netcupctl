"""Snapshot management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id, validate_snapshot_name


@click.group()
def snapshots():
    """Snapshot management commands.

    Create, manage, and restore server snapshots.
    """
    pass


@snapshots.command("list")
@click.argument("server_id")
@click.pass_obj
def list_snapshots(ctx, server_id: str):
    """List all snapshots for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/snapshots")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@snapshots.command("get")
@click.argument("server_id")
@click.argument("name")
@click.pass_obj
def get_snapshot(ctx, server_id: str, name: str):
    """Get details for a specific snapshot.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        NAME: The name of the snapshot
    """
    try:
        server_id = validate_server_id(server_id)
        name = validate_snapshot_name(name)
        result = ctx.client.get(f"/api/v1/servers/{server_id}/snapshots/{name}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@snapshots.command("create")
@click.argument("server_id")
@click.option("--name", required=True, help="Name for the snapshot")
@click.option("--description", default="", help="Description for the snapshot")
@click.option("--dry-run", is_flag=True, help="Check if snapshot creation is possible")
@click.pass_obj
def create_snapshot(
    ctx, server_id: str, name: str, description: str, dry_run: bool
):
    """Create a new snapshot.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        name = validate_snapshot_name(name)

        if dry_run:
            result = ctx.client.post(
                f"/api/v1/servers/{server_id}/snapshots:dryrun",
                json={"name": name, "description": description},
            )
            ctx.formatter.output(result)
            click.echo("\n[OK] Dry run completed - snapshot can be created.", err=False)
        else:
            result = ctx.client.post(
                f"/api/v1/servers/{server_id}/snapshots",
                json={"name": name, "description": description},
            )
            ctx.formatter.output(result)
            click.echo("\n[OK] Snapshot creation initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@snapshots.command("delete")
@click.argument("server_id")
@click.argument("name")
@click.option("--confirm", is_flag=True, help="Confirm the delete operation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def delete_snapshot(ctx, server_id: str, name: str, confirm: bool, yes: bool):
    """Delete a snapshot.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        NAME: The name of the snapshot to delete
    """
    try:
        server_id = validate_server_id(server_id)
        name = validate_snapshot_name(name)

        if not confirm and not yes:
            if not click.confirm(f"Delete snapshot '{name}'? This cannot be undone."):
                raise click.Abort()

        result = ctx.client.delete(f"/api/v1/servers/{server_id}/snapshots/{name}")
        ctx.formatter.output(result)
        click.echo("\n[OK] Snapshot deleted.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@snapshots.command("revert")
@click.argument("server_id")
@click.argument("name")
@click.option("--confirm", is_flag=True, help="Confirm the revert operation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def revert_snapshot(ctx, server_id: str, name: str, confirm: bool, yes: bool):
    """Revert server to a snapshot (DESTRUCTIVE).

    WARNING: Current server state will be lost!

    \b
    Arguments:
        SERVER_ID: The ID of the server
        NAME: The name of the snapshot to revert to
    """
    try:
        server_id = validate_server_id(server_id)
        name = validate_snapshot_name(name)

        if not confirm and not yes:
            if not click.confirm(
                f"Revert to snapshot '{name}'? Current server state will be LOST!"
            ):
                raise click.Abort()

        result = ctx.client.post(f"/api/v1/servers/{server_id}/snapshots/{name}/revert")
        ctx.formatter.output(result)
        click.echo("\n[OK] Snapshot revert initiated.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@snapshots.command("export")
@click.argument("server_id")
@click.argument("name")
@click.pass_obj
def export_snapshot(ctx, server_id: str, name: str):
    """Export a snapshot.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        NAME: The name of the snapshot to export
    """
    try:
        server_id = validate_server_id(server_id)
        name = validate_snapshot_name(name)
        result = ctx.client.post(f"/api/v1/servers/{server_id}/snapshots/{name}/export")
        ctx.formatter.output(result)
        click.echo("\n[OK] Snapshot export initiated.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@snapshots.command("dryrun")
@click.argument("server_id")
@click.option("--name", required=True, help="Name for the snapshot to test")
@click.option("--description", default="", help="Description for the snapshot")
@click.pass_obj
def dryrun_snapshot(ctx, server_id: str, name: str, description: str):
    """Test if a snapshot can be created (dry run).

    Validates that a snapshot with the given name can be created
    without actually creating it.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        name = validate_snapshot_name(name)
        result = ctx.client.post(
            f"/api/v1/servers/{server_id}/snapshots:dryrun",
            json={"name": name, "description": description},
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Dry run completed - snapshot can be created.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
