"""User firewall policy management commands."""

import json
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.group(name="firewall-policies")
def firewall_policies():
    """Firewall policy management commands.

    Manage user-level firewall policies.
    """
    pass


@firewall_policies.command("list")
@click.option("--search", "-q", help="Search query")
@click.option("--limit", type=int, default=50, help="Maximum number of policies (default: 50)")
@click.option("--offset", type=int, default=0, help="Number of policies to skip (default: 0)")
@click.pass_obj
def list_policies(ctx, search: str, limit: int, offset: int):
    """List firewall policies."""
    try:
        user_id = get_authenticated_user_id(ctx)
        params = {"limit": limit, "offset": offset}
        if search:
            params["q"] = search

        result = ctx.client.get(f"/api/v1/users/{user_id}/firewall-policies", params=params)
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall_policies.command("get")
@click.argument("policy_id")
@click.option("--with-count", is_flag=True, help="Include count of affected servers")
@click.pass_obj
def get_policy(ctx, policy_id: str, with_count: bool):
    """Get details for a specific firewall policy.

    \b
    Arguments:
        POLICY_ID: The ID of the policy
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        params = {"withCountOfAffectedServers": "true"} if with_count else None
        result = ctx.client.get(
            f"/api/v1/users/{user_id}/firewall-policies/{policy_id}", params=params
        )
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall_policies.command("create")
@click.option("--name", required=True, help="Name for the policy")
@click.option("--rules", help="Policy rules as JSON string")
@click.option("--rules-file", type=click.File("r"), help="Policy rules from JSON file")
@click.pass_obj
def create_policy(ctx, name: str, rules: str, rules_file):
    """Create a new firewall policy.

    Provide rules as a JSON string or from a file.
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        if rules_file:
            rules_data = json.load(rules_file)
        elif rules:
            rules_data = json.loads(rules)
        else:
            rules_data = {}

        policy_data = {"name": name, **rules_data}
        result = ctx.client.post(
            f"/api/v1/users/{user_id}/firewall-policies", json=policy_data
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Firewall policy created.", err=False)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {e}", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall_policies.command("update")
@click.argument("policy_id")
@click.option("--name", help="New name for the policy")
@click.option("--rules", help="Policy rules as JSON string")
@click.option("--rules-file", type=click.File("r"), help="Policy rules from JSON file")
@click.pass_obj
def update_policy(ctx, policy_id: str, name: str, rules: str, rules_file):
    """Update a firewall policy.

    \b
    Arguments:
        POLICY_ID: The ID of the policy to update
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        policy_data = {}

        if name:
            policy_data["name"] = name

        if rules_file:
            policy_data.update(json.load(rules_file))
        elif rules:
            policy_data.update(json.loads(rules))

        if not policy_data:
            raise click.UsageError("Provide at least one update option (--name, --rules, --rules-file)")

        result = ctx.client.put(
            f"/api/v1/users/{user_id}/firewall-policies/{policy_id}", json=policy_data
        )
        ctx.formatter.output(result)
        click.echo("\n[OK] Firewall policy updated.", err=False)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {e}", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall_policies.command("delete")
@click.argument("policy_id")
@click.option("--confirm", is_flag=True, help="Confirm the delete operation")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def delete_policy(ctx, policy_id: str, confirm: bool, yes: bool):
    """Delete a firewall policy.

    \b
    Arguments:
        POLICY_ID: The ID of the policy to delete
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        if not confirm and not yes:
            if not click.confirm(f"Delete firewall policy '{policy_id}'? This cannot be undone."):
                raise click.Abort()

        result = ctx.client.delete(f"/api/v1/users/{user_id}/firewall-policies/{policy_id}")
        ctx.formatter.output(result)
        click.echo("\n[OK] Firewall policy deleted.", err=False)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
