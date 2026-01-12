"""Server metrics commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_server_id


@click.group()
def metrics():
    """Server metrics commands.

    View CPU, disk, and network metrics for your servers.
    """
    pass


@metrics.command("cpu")
@click.argument("server_id")
@click.option(
    "--hours",
    type=int,
    default=24,
    help="Number of hours of data to retrieve (default: 24)",
)
@click.pass_obj
def cpu_metrics(ctx, server_id: str, hours: int):
    """View CPU metrics for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        params = {"hours": hours}
        result = ctx.client.get(f"/api/v1/servers/{server_id}/metrics/cpu", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@metrics.command("disk")
@click.argument("server_id")
@click.option(
    "--hours",
    type=int,
    default=24,
    help="Number of hours of data to retrieve (default: 24)",
)
@click.pass_obj
def disk_metrics(ctx, server_id: str, hours: int):
    """View disk I/O metrics for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        params = {"hours": hours}
        result = ctx.client.get(f"/api/v1/servers/{server_id}/metrics/disk", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@metrics.command("network")
@click.argument("server_id")
@click.option(
    "--hours",
    type=int,
    default=24,
    help="Number of hours of data to retrieve (default: 24)",
)
@click.pass_obj
def network_metrics(ctx, server_id: str, hours: int):
    """View network metrics for a server.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        params = {"hours": hours}
        result = ctx.client.get(
            f"/api/v1/servers/{server_id}/metrics/network", params=params
        )
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@metrics.command("network-packets")
@click.argument("server_id")
@click.option(
    "--hours",
    type=int,
    default=24,
    help="Number of hours of data to retrieve (default: 24)",
)
@click.pass_obj
def network_packet_metrics(ctx, server_id: str, hours: int):
    """View network packet metrics for a server.

    Shows packet-level network statistics.

    \b
    Arguments:
        SERVER_ID: The ID of the server
    """
    try:
        server_id = validate_server_id(server_id)
        params = {"hours": hours}
        result = ctx.client.get(
            f"/api/v1/servers/{server_id}/metrics/network/packet", params=params
        )
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
