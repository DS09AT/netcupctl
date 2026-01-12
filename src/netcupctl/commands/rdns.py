"""Reverse DNS management commands."""

import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_ip


@click.group()
def rdns():
    """Reverse DNS management commands.

    Manage rDNS entries for your IP addresses.
    """
    pass


@rdns.command("get")
@click.argument("ip")
@click.pass_obj
def get_rdns(ctx, ip: str):
    """Get rDNS entry for an IP address.

    Automatically detects IPv4 or IPv6.

    \b
    Arguments:
        IP: The IP address (IPv4 or IPv6)
    """
    try:
        validated_ip, version = validate_ip(ip)
        endpoint = f"/api/v1/rdns/ipv{version[1]}/{validated_ip}"
        result = ctx.client.get(endpoint)
        ctx.formatter.output(result)
    except APIError as e:
        if e.status_code == 404:
            click.echo(f"No rDNS entry found for {ip}")
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(e.status_code or 1)


@rdns.command("set")
@click.argument("ip")
@click.option("--hostname", required=True, help="The hostname for the rDNS entry")
@click.pass_obj
def set_rdns(ctx, ip: str, hostname: str):
    """Set rDNS entry for an IP address.

    Automatically detects IPv4 or IPv6.

    \b
    Arguments:
        IP: The IP address (IPv4 or IPv6)
    """
    try:
        validated_ip, version = validate_ip(ip)
        endpoint = f"/api/v1/rdns/ipv{version[1]}"
        result = ctx.client.post(endpoint, json={"ip": validated_ip, "rdns": hostname})
        ctx.formatter.output(result)
        click.echo(f"\n[OK] rDNS entry set for {validated_ip}", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@rdns.command("delete")
@click.argument("ip")
@click.pass_obj
def delete_rdns(ctx, ip: str):
    """Delete rDNS entry for an IP address.

    Automatically detects IPv4 or IPv6.

    \b
    Arguments:
        IP: The IP address (IPv4 or IPv6)
    """
    try:
        validated_ip, version = validate_ip(ip)
        endpoint = f"/api/v1/rdns/ipv{version[1]}/{validated_ip}"
        result = ctx.client.delete(endpoint)
        ctx.formatter.output(result)
        click.echo(f"\n[OK] rDNS entry deleted for {validated_ip}", err=False)
    except APIError as e:
        if e.status_code == 404:
            click.echo(f"No rDNS entry found for {ip}")
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(e.status_code or 1)
