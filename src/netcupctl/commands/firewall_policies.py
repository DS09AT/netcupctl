"""User firewall policy management commands."""

import json
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id, upsert_policy


@click.group(name="firewall-policies")
def firewall_policies():
    """Firewall policy management commands.

    Manage user-level firewall policies. A policy contains an ordered list of
    firewall rules. Policies are then assigned to a server interface with the
    'netcupctl firewall set' command.

    \b
    Typical workflow:
      1. Create a policy:  netcupctl firewall-policies create --name "web" --rules-file policy.json
      2. Get the ID:       netcupctl firewall-policies list
      3. Assign it:        netcupctl firewall set SERVER_ID MAC --rules '{"copiedPolicies":[],"userPolicies":[{"id":42}],"active":true}'
    """
    pass


@firewall_policies.command("list")
@click.option("--search", "-q", help="Search term to filter policies by name.")
@click.option("--limit", type=int, default=50, help="Maximum number of results (default: 50).")
@click.option("--offset", type=int, default=0, help="Offset for pagination (default: 0).")
@click.pass_obj
def list_policies(ctx, search: str, limit: int, offset: int):
    """List all firewall policies.

    \b
    Examples:
      netcupctl firewall-policies list
      netcupctl firewall-policies list --search web
      netcupctl --format json firewall-policies list
      netcupctl firewall-policies list --limit 10 --offset 20
    """
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
@click.option("--with-count", is_flag=True, help="Include the number of affected servers.")
@click.pass_obj
def get_policy(ctx, policy_id: str, with_count: bool):
    """Get details for a specific firewall policy.

    Shows all rules of the policy including direction, protocol, action, and
    source and destination addresses.

    \b
    Arguments:
        POLICY_ID: Numeric policy ID (from 'firewall-policies list').

    \b
    Examples:
      netcupctl firewall-policies get 42
      netcupctl firewall-policies get 42 --with-count
      netcupctl --format json firewall-policies get 42
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
@click.option("--name", required=True, help="Name of the new policy.")
@click.option("--rules", help="Policy configuration as a JSON string.")
@click.option("--rules-file", type=click.File("r"), help="Policy configuration from a JSON file.")
@click.pass_obj
def create_policy(ctx, name: str, rules: str, rules_file):
    """Create a new firewall policy.

    Creates a policy with optional firewall rules. Without --rules or
    --rules-file an empty policy is created.

    \b
    JSON format (--rules or --rules-file):
      {
        "rules": [
          {
            "direction":        "INGRESS",
            "protocol":         "TCP",
            "action":           "ACCEPT",
            "sources":          ["0.0.0.0/0"],
            "sourcePorts":      null,
            "destinations":     [],
            "destinationPorts": "443",
            "description":      "Allow HTTPS"
          }
        ]
      }

    \b
    Rule fields (FirewallRule):
      direction         INGRESS | EGRESS                           [required]
      protocol          TCP | UDP | ICMP | ICMPv6                  [required]
      action            ACCEPT | DROP                              [required]
      sources           IPv4/IPv6 addresses or CIDR ranges         [optional, [] = any]
      sourcePorts       Single port ("80") or range ("1024-65535") [optional, null = any]
      destinations      IPv4/IPv6 addresses or CIDR ranges         [optional, [] = any]
      destinationPorts  Single port ("443") or range ("8080-8090") [optional, null = any]
      description       Free text label                            [optional]

    \b
    IP address formats:
      IPv4 address:  "192.168.10.1"
      IPv4 network:  "192.168.10.0/24"
      IPv6 address:  "0092:e10f:cb66:35a9::"
      IPv6 prefix:   "0092:e10f:cb66:35a9::/64"
      Any address:   null or []

    \b
    API constraints (validated server-side):
      Max 500 rules per policy; each source or destination counts as one rule.
      Multiple sources require the destination to be empty (any) or a single IP/network.
      Multiple destinations require the source to be empty (any) or a single IP/network.
      Mixing IPv4 and IPv6 in sources requires destinations to be empty (any).
      Mixing IPv4 and IPv6 in destinations requires sources to be empty (any).
      ICMP and ICMPv6 rules do not support port fields.

    \b
    Examples:
      netcupctl firewall-policies create --name "my-policy"
      netcupctl firewall-policies create --name "web" --rules-file policy.json
      netcupctl firewall-policies create --name "ssh" --rules '{"rules":[{"direction":"INGRESS","protocol":"TCP","action":"ACCEPT","sources":[],"destinationPorts":"22"}]}'
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
@click.option("--name", help="New name for the policy.")
@click.option("--rules", help="Policy configuration as a JSON string (replaces all rules).")
@click.option("--rules-file", type=click.File("r"), help="Policy configuration from a JSON file.")
@click.pass_obj
def update_policy(ctx, policy_id: str, name: str, rules: str, rules_file):
    """Update a firewall policy.

    Updates the name and/or rules of an existing policy. Providing --rules or
    --rules-file replaces the entire rule list; there is no partial merge.

    \b
    Arguments:
        POLICY_ID: Numeric policy ID (from 'firewall-policies list').

    \b
    JSON format (--rules or --rules-file) is identical to 'create':
      {
        "rules": [
          {
            "direction":        "EGRESS",
            "protocol":         "TCP",
            "action":           "ACCEPT",
            "sources":          [],
            "destinations":     [],
            "destinationPorts": "80",
            "description":      "Allow outbound HTTP"
          }
        ]
      }

    \b
    Rule fields (FirewallRule):
      direction         INGRESS | EGRESS                           [required]
      protocol          TCP | UDP | ICMP | ICMPv6                  [required]
      action            ACCEPT | DROP                              [required]
      sources           IPv4/IPv6 addresses or CIDR ranges         [optional, [] = any]
      sourcePorts       Single port ("80") or range ("1024-65535") [optional, null = any]
      destinations      IPv4/IPv6 addresses or CIDR ranges         [optional, [] = any]
      destinationPorts  Single port ("443") or range ("8080-8090") [optional, null = any]
      description       Free text label                            [optional]

    \b
    API constraints (validated server-side):
      Max 500 rules per policy; each source or destination counts as one rule.
      Multiple sources require the destination to be empty (any) or a single IP/network.
      Multiple destinations require the source to be empty (any) or a single IP/network.
      Mixing IPv4 and IPv6 in sources requires destinations to be empty (any).
      Mixing IPv4 and IPv6 in destinations requires sources to be empty (any).
      ICMP and ICMPv6 rules do not support port fields.

    \b
    Examples:
      netcupctl firewall-policies update 42 --name "new-name"
      netcupctl firewall-policies update 42 --rules-file updated_policy.json
      netcupctl firewall-policies update 42 --rules '{"rules":[{"direction":"EGRESS","protocol":"TCP","action":"ACCEPT","sources":[],"destinations":[],"destinationPorts":"80"}]}'
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


@firewall_policies.command("upsert")
@click.option("--name", required=True, help="Name of the policy to create or update.")
@click.option("--rules", help="Policy rules as a JSON string.")
@click.option("--rules-file", type=click.File("r"), help="Policy rules from a JSON file.")
@click.pass_obj
def upsert_policy_cmd(ctx, name: str, rules: str, rules_file):
    """Create a policy if it does not exist, or update it if it does (upsert).

    The policy is identified by its exact name. If no policy with that name
    exists a new one is created; if exactly one match is found it is updated
    in place (all existing rules are replaced). The command exits with an error
    if multiple policies share the same name.

    The numeric policy ID is printed to stdout so it can be captured in a shell
    script. The status message is written to stderr and does not interfere with
    the captured output.

    \b
    Idempotency: running this command twice with the same arguments produces the
    same result and returns the same policy ID both times.

    \b
    For the rule JSON format, see: netcupctl firewall-policies create --help

    \b
    Examples:
      POLICY_ID=$(netcupctl firewall-policies upsert --name "ssh-only" --rules-file rules.json)
      netcupctl firewall-policies upsert --name "web" --rules '{"rules":[{"direction":"INGRESS","protocol":"TCP","action":"ACCEPT","sources":[],"destinationPorts":"443"}]}'
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        if rules_file:
            rules_data = json.load(rules_file)
        elif rules:
            rules_data = json.loads(rules)
        else:
            rules_data = {}

        policy_id = upsert_policy(ctx, user_id, name, rules_data)
        click.echo(policy_id)
        click.echo(f"[OK] Policy upserted (id={policy_id}).", err=True)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {e}", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@firewall_policies.command("delete")
@click.argument("policy_id")
@click.option("--confirm", is_flag=True, help="Confirm the delete operation (non-interactive).")
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_obj
def delete_policy(ctx, policy_id: str, confirm: bool, yes: bool):
    """Delete a firewall policy.

    Permanently deletes a policy. Policies that are still assigned to an
    interface cannot be deleted.

    \b
    Arguments:
        POLICY_ID: Numeric policy ID (from 'firewall-policies list').

    \b
    Examples:
      netcupctl firewall-policies delete 42
      netcupctl firewall-policies delete 42 --yes
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
