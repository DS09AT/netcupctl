"""Custom image management commands."""

import os
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.group(name="custom-images")
def custom_images():
    """Custom image management commands.

    Manage custom OS images uploaded to your account.
    """
    pass


@custom_images.command("list")
@click.pass_obj
def list_images(ctx):
    """List all custom images."""
    try:
        user_id = get_authenticated_user_id(ctx)
        result = ctx.client.get(f"/api/v1/users/{user_id}/images")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@custom_images.command("get")
@click.argument("key")
@click.pass_obj
def get_image(ctx, key: str):
    """Get details for a custom image.

    \b
    Arguments:
        KEY: The key/name of the custom image
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        result = ctx.client.get(f"/api/v1/users/{user_id}/images/{key}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@custom_images.command("delete")
@click.argument("key")
@click.option("--confirm", is_flag=True, help="Confirm the delete operation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def delete_image(ctx, key: str, confirm: bool, yes: bool):
    """Delete a custom image.

    \b
    Arguments:
        KEY: The key/name of the custom image to delete
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        if not confirm and not yes:
            if not click.confirm(f"Delete custom image '{key}'? This cannot be undone."):
                raise click.Abort()

        result = ctx.client.delete(f"/api/v1/users/{user_id}/images/{key}")
        ctx.formatter.output(result)
        click.echo("\n[OK] Custom image deleted.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@custom_images.command("upload")
@click.argument("file", type=click.Path(exists=True))
@click.option("--name", help="Image name (defaults to filename)")
@click.pass_obj
def upload_image(ctx, file: str, name: str):
    """Upload a custom image (multipart upload).

    Uploads a custom OS image file to your account.
    Supports large files via multipart upload.

    \b
    Arguments:
        FILE: Path to the image file to upload
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        key = name or os.path.basename(file)
        file_size = os.path.getsize(file)

        click.echo(f"Uploading {key} ({file_size / (1024*1024):.1f} MB)...")

        init_result = ctx.client.post(f"/api/v1/users/{user_id}/images/{key}")
        upload_id = init_result.get("uploadId")

        if not upload_id:
            click.echo("Error: Failed to initiate upload", err=True)
            sys.exit(1)

        try:
            chunk_size = 100 * 1024 * 1024
            parts = []
            part_number = 1

            with open(file, "rb") as f:
                with click.progressbar(length=file_size, label="Uploading") as bar:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break

                        part_result = ctx.client.put_binary(
                            f"/api/v1/users/{user_id}/images/{key}/{upload_id}/parts/{part_number}",
                            data=chunk,
                        )

                        etag = part_result.get("etag") or part_result.get("ETag")
                        parts.append({"partNumber": part_number, "etag": etag})

                        bar.update(len(chunk))
                        part_number += 1

            complete_result = ctx.client.post(
                f"/api/v1/users/{user_id}/images/{key}/{upload_id}",
                json={"parts": parts}
            )

            ctx.formatter.output(complete_result)
            click.echo("\n[OK] Custom image uploaded successfully.", err=False)

        except Exception as e:
            click.echo(f"\nUpload failed: {e}", err=True)
            click.echo("Aborting upload...", err=True)
            try:
                ctx.client.delete(f"/api/v1/users/{user_id}/images/{key}/{upload_id}")
            except Exception:
                pass
            sys.exit(1)

    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
