"""Server firewall management commands."""

import json
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.validators import validate_mac_address, validate_server_id


@click.group()
def firewall():
    """Server firewall management commands.

    Manage firewall rules for server network interfaces.
    """
    pass


@firewall.command("show")
@click.argument("server_id")
@click.argument("mac")
@click.option("--check", is_flag=True, help="Include consistency check")
@click.pass_obj
def show_firewall(ctx, server_id: str, mac: str, check: bool):
    """Show firewall rules for a server interface.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        MAC: The MAC address of the interface
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)
        params = {"consistencyCheck": "true"} if check else None
        result = ctx.client.get(
            f"/api/v1/servers/{server_id}/interfaces/{mac}/firewall", params=params
        )
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall.command("set")
@click.argument("server_id")
@click.argument("mac")
@click.option("--rules", help="Firewall rules as JSON string")
@click.option("--rules-file", type=click.File("r"), help="Firewall rules from JSON file")
@click.pass_obj
def set_firewall(ctx, server_id: str, mac: str, rules: str, rules_file):
    """Set firewall rules for a server interface.

    Provide rules as a JSON string or from a file.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        MAC: The MAC address of the interface
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)

        if rules_file:
            rules_data = json.load(rules_file)
        elif rules:
            rules_data = json.loads(rules)
        else:
            raise click.UsageError("Provide --rules or --rules-file")

        result = ctx.client.put(
            f"/api/v1/servers/{server_id}/interfaces/{mac}/firewall", json=rules_data
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Firewall rules updated.", err=False)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {e}", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall.command("reapply")
@click.argument("server_id")
@click.argument("mac")
@click.pass_obj
def reapply_firewall(ctx, server_id: str, mac: str):
    """Reapply firewall rules for a server interface.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        MAC: The MAC address of the interface
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)
        result = ctx.client.post(
            f"/api/v1/servers/{server_id}/interfaces/{mac}/firewall:reapply"
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Firewall rules reapplied.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall.command("restore")
@click.argument("server_id")
@click.argument("mac")
@click.pass_obj
def restore_firewall(ctx, server_id: str, mac: str):
    """Restore copied firewall policies for a server interface.

    \b
    Arguments:
        SERVER_ID: The ID of the server
        MAC: The MAC address of the interface
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)
        result = ctx.client.post(
            f"/api/v1/servers/{server_id}/interfaces/{mac}/firewall:restore-copied-policies"
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Firewall policies restored.", err=False)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
