"""OpenAPI specification management commands."""

import sys
from pathlib import Path

import click

import netcupctl
from netcupctl.spec_manager import SpecError, SpecManager


@click.group()
def spec():
    """OpenAPI specification management.

    Manage the local OpenAPI specification file used for API documentation
    and client code generation.
    """
    pass


@spec.command()
def update():
    """Download/update OpenAPI specification.

    Downloads the latest OpenAPI spec from the netcup public API
    and updates the local copy if the version has changed. Version comparison uses
    the info.version field from the OpenAPI specification.

    The spec file is stored in the data/ directory of the project.
    """
    try:
        package_dir = Path(netcupctl.__file__).parent
        project_root = package_dir.parent.parent
        data_dir = project_root / "data"

        manager = SpecManager(data_dir)
        result = manager.update_spec()

        if result["status"] == "first_download":
            click.echo("[OK] OpenAPI specification downloaded successfully.")
            click.echo(f"Version: {result['remote_version']}")  # pylint: disable=inconsistent-quotes
            click.echo(f"Location: {manager.spec_file}")

        elif result["status"] == "updated":
            click.echo("[OK] OpenAPI specification updated.")
            click.echo(f"Previous version: {result['local_version']}")  # pylint: disable=inconsistent-quotes
            click.echo(f"Current version:  {result['remote_version']}")  # pylint: disable=inconsistent-quotes
            click.echo(f"Location: {manager.spec_file}")

        else:
            click.echo("[OK] OpenAPI specification is already up to date.")
            click.echo(f"Version: {result['local_version']}")  # pylint: disable=inconsistent-quotes

    except SpecError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@spec.command()
def show():
    """Show current OpenAPI specification version.

    Displays the version of the locally stored OpenAPI specification.
    """
    try:
        package_dir = Path(netcupctl.__file__).parent
        project_root = package_dir.parent.parent
        data_dir = project_root / "data"

        manager = SpecManager(data_dir)
        version = manager.get_local_version()

        if version:
            click.echo(f"OpenAPI Specification Version: {version}")
            click.echo(f"Location: {manager.spec_file}")
        else:
            click.echo("No OpenAPI specification found.")
            click.echo(f"Expected location: {manager.spec_file}")
            click.echo("\nRun 'netcupctl spec update' to download it.")

    except SpecError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
