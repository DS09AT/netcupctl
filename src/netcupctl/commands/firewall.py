"""Server firewall management commands."""

import json
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id, upsert_policy
from netcupctl.commands.validators import validate_mac_address, validate_server_id

_CLEANUP_PAGE_SIZE = 100


def _load_rules(rules: str, rules_file) -> dict:
    if rules_file:
        return json.load(rules_file)
    if rules:
        return json.loads(rules)
    return {}


def _extract_copied_ids(current: dict) -> list:
    return [{"id": p["id"]} for p in current.get("copiedPolicies", []) if p.get("id") is not None]


def _collect_all_policies(ctx, user_id: str) -> dict:
    """Return all user policies as a dict mapping policy ID to policy name. Paginates automatically."""
    policies = {}
    offset = 0
    while True:
        page = ctx.client.get(
            f"/api/v1/users/{user_id}/firewall-policies",
            params={"limit": _CLEANUP_PAGE_SIZE, "offset": offset},
        )
        page_list = page if isinstance(page, list) else []
        for pol in page_list:
            policies[pol["id"]] = pol.get("name", "")
        if len(page_list) < _CLEANUP_PAGE_SIZE:
            break
        offset += _CLEANUP_PAGE_SIZE
    return policies


def _policy_ids_from_firewall(fw: dict) -> set:
    combined = fw.get("userPolicies", []) + fw.get("copiedPolicies", [])
    return {p["id"] for p in combined if p.get("id") is not None}


def _policy_ids_for_interface(ctx, server_id: str, mac: str) -> set:
    try:
        fw = ctx.client.get(f"/api/v1/servers/{server_id}/interfaces/{mac}/firewall")
        return _policy_ids_from_firewall(fw)
    except APIError:
        return set()


def _firewall_policy_ids_for_server(ctx, server_id: str) -> set:
    try:
        interfaces = ctx.client.get(f"/api/v1/servers/{server_id}/interfaces")
    except APIError:
        return set()
    iface_list = interfaces if isinstance(interfaces, list) else []
    ids = set()
    for iface in iface_list:
        mac = iface.get("mac")
        if mac:
            ids.update(_policy_ids_for_interface(ctx, server_id, mac))
    return ids


def _collect_referenced_ids(ctx) -> set:
    try:
        result = ctx.client.get("/api/v1/servers")
    except APIError:
        return set()
    servers = result if isinstance(result, list) else []
    ids = set()
    for server in servers:
        server_id = server.get("id")
        if server_id:
            ids.update(_firewall_policy_ids_for_server(ctx, server_id))
    return ids


def _print_orphaned(orphaned: dict, dry_run: bool) -> None:
    for pol_id, pol_name in orphaned.items():
        prefix = "Would delete" if dry_run else "Deleting"
        click.echo(f"  {prefix}: policy {pol_id} ({pol_name})")


def _confirm_deletion(orphaned: dict, yes: bool) -> bool:
    if yes:
        return True
    return click.confirm(f"Delete {len(orphaned)} orphaned policies?")


def _execute_deletions(ctx, user_id: str, orphaned: dict) -> None:
    for pol_id in orphaned:
        ctx.client.delete(f"/api/v1/users/{user_id}/firewall-policies/{pol_id}")
        click.echo(f"[OK] Deleted policy {pol_id}.")


def _delete_policies(ctx, user_id: str, orphaned: dict, dry_run: bool, yes: bool) -> None:
    if not orphaned:
        click.echo("No orphaned firewall policies found.")
        return
    _print_orphaned(orphaned, dry_run)
    if dry_run:
        return
    if not _confirm_deletion(orphaned, yes):
        raise click.Abort()
    _execute_deletions(ctx, user_id, orphaned)


@click.group()
def firewall():
    """Server firewall management commands.

    Manage firewall rules for server network interfaces.
    Each interface has its own firewall that references user-defined policies.
    Use the 'firewall-policies' commands to create and manage the actual rules.

    The netcup API uses a two-step workflow: rules are defined inside policies
    (via 'firewall-policies create'), and policies are then assigned to an
    interface by their numeric ID (via 'firewall set'). The 'firewall configure'
    command combines both steps into a single idempotent operation.
    """
    pass


@firewall.command("show")
@click.argument("server_id")
@click.argument("mac")
@click.option("--check", is_flag=True, help="Check whether rules have actually been applied.")
@click.pass_obj
def show_firewall(ctx, server_id: str, mac: str, check: bool):
    """Show firewall rules for a server interface.

    \b
    Arguments:
        SERVER_ID: Numeric server ID.
        MAC:       MAC address of the network interface (e.g. aa:bb:cc:dd:ee:ff).

    \b
    Response fields:
      copiedPolicies      Copied firewall policies with their rules.
      userPolicies        User-owned firewall policies with their rules.
      ingressImplicitRule Default implicit rule for incoming traffic (read-only).
      egressImplicitRule  Default implicit rule for outgoing traffic (read-only).
      consistent          True if rules have been applied (only with --check).
      active              True if the firewall is currently active.

    \b
    Examples:
      netcupctl firewall show 12345 aa:bb:cc:dd:ee:ff
      netcupctl firewall show 12345 aa:bb:cc:dd:ee:ff --check
      netcupctl --format json firewall show 12345 aa:bb:cc:dd:ee:ff
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
@click.option("--rules", help="Firewall configuration as a JSON string.")
@click.option("--rules-file", type=click.File("r"), help="Firewall configuration from a JSON file.")
@click.pass_obj
def set_firewall(ctx, server_id: str, mac: str, rules: str, rules_file):
    """Set firewall configuration for a server interface.

    Assigns firewall policies to an interface by their numeric IDs. The actual
    rules live inside policies, which are managed with the 'firewall-policies'
    commands. For a single-step workflow that creates or updates the policy and
    assigns it atomically, use 'firewall configure' instead.

    \b
    Arguments:
        SERVER_ID: Numeric server ID.
        MAC:       MAC address of the network interface (e.g. aa:bb:cc:dd:ee:ff).

    \b
    JSON format (--rules or --rules-file):
      {
        "copiedPolicies": [{"id": 123}],
        "userPolicies":   [{"id": 42}, {"id": 99}],
        "active": true
      }

    \b
    Fields:
      copiedPolicies  array of {id:int}  Copied policies. Must be present; use [] for none.
      userPolicies    array of {id:int}  User-owned policies. Must be present; use [] for none.
      active          bool               Whether the firewall is active (default: true).

    \b
    Notes:
      Policy IDs can be retrieved with: netcupctl firewall-policies list
      The order of IDs determines rule priority: the first entry has the highest priority.
      Changes are applied asynchronously (the API returns HTTP 202 with a task reference).
      If a policy update times out due to a concurrent write operation, run:
      netcupctl firewall reapply SERVER_ID MAC
      The API automatically sets ingressImplicitRule to DROP_ALL when at least one policy
      is assigned, and to ACCEPT_ALL when both userPolicies and copiedPolicies are empty.
      This command prints a warning when the submitted configuration would leave both
      arrays empty, because that removes all rules and opens the interface to all traffic.

    \b
    Examples:
      netcupctl firewall set 12345 aa:bb:cc:dd:ee:ff --rules-file firewall.json
      netcupctl firewall set 12345 aa:bb:cc:dd:ee:ff --rules '{"copiedPolicies":[],"userPolicies":[{"id":42}],"active":true}'
      netcupctl firewall set 12345 aa:bb:cc:dd:ee:ff --rules '{"copiedPolicies":[],"userPolicies":[],"active":false}'
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

        if not rules_data.get("userPolicies") and not rules_data.get("copiedPolicies"):
            click.echo(
                "Warning: assigning no policies removes all firewall rules "
                "and results in ACCEPT_ALL (all traffic is allowed).",
                err=True,
            )

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


@firewall.command("configure")
@click.argument("server_id")
@click.argument("mac")
@click.option("--name", required=True, help="Name of the firewall policy to create or update.")
@click.option("--rules", help="Policy rules as a JSON string.")
@click.option("--rules-file", type=click.File("r"), help="Policy rules from a JSON file.")
@click.option(
    "--active/--no-active",
    default=True,
    help="Enable or disable the firewall after assignment (default: active).",
)
@click.pass_obj
def configure_firewall(ctx, server_id: str, mac: str, name: str, rules: str, rules_file, active: bool):
    """Create or update a named policy and assign it to a server interface atomically.

    This command combines the two steps the netcup API requires into one
    idempotent operation. It first creates or updates the named policy (via
    'firewall-policies'), then assigns it as the sole user policy on the
    given interface. Existing copied policies on the interface are preserved.

    When to use this command instead of 'firewall set':
    Use 'firewall configure' when you want to manage rules declaratively from a
    file or script without manually tracking policy IDs. Use 'firewall set' when
    you are directly managing policy assignments by ID (for example, assigning
    multiple pre-existing policies in a specific order).

    Implicit rules:
    The API automatically applies DROP_ALL as the implicit rule for both ingress
    and egress when at least one policy is assigned. Since this command always
    assigns exactly one policy, the result is always DROP_ALL after a successful
    configure. Implicit rules cannot be set via PUT and are not configurable.

    For the policy rule format, see: netcupctl firewall-policies create --help

    \b
    Arguments:
        SERVER_ID: Numeric server ID.
        MAC:       MAC address of the network interface (e.g. aa:bb:cc:dd:ee:ff).

    \b
    Examples:
      netcupctl firewall configure 12345 aa:bb:cc:dd:ee:ff --name "ssh-only" --rules-file rules.json
      netcupctl firewall configure 12345 aa:bb:cc:dd:ee:ff --name "web" --rules '{"rules":[{"direction":"INGRESS","protocol":"TCP","action":"ACCEPT","sources":[],"destinationPorts":"443"}]}'
      netcupctl firewall configure 12345 aa:bb:cc:dd:ee:ff --name "web" --no-active
    """
    try:
        server_id = validate_server_id(server_id)
        mac = validate_mac_address(mac)
        rules_data = _load_rules(rules, rules_file)
        user_id = get_authenticated_user_id(ctx)
        policy_id = upsert_policy(ctx, user_id, name, rules_data)
        current = ctx.client.get(f"/api/v1/servers/{server_id}/interfaces/{mac}/firewall")
        copied_ids = _extract_copied_ids(current)
        ctx.client.put(
            f"/api/v1/servers/{server_id}/interfaces/{mac}/firewall",
            json={
                "copiedPolicies": copied_ids,
                "userPolicies": [{"id": policy_id}],
                "active": active,
            },
        )
        click.echo(f'[OK] Firewall configured. Policy "{name}" (id={policy_id}) assigned to {mac}.')
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

    Use this when a policy update timed out because of a long-running write
    operation on the server (for example, a storage optimization).

    \b
    Arguments:
        SERVER_ID: Numeric server ID.
        MAC:       MAC address of the network interface (e.g. aa:bb:cc:dd:ee:ff).

    \b
    Example:
      netcupctl firewall reapply 12345 aa:bb:cc:dd:ee:ff
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

    Use this when copied policies on an interface are out of date because the
    original policy was modified.

    \b
    Arguments:
        SERVER_ID: Numeric server ID.
        MAC:       MAC address of the network interface (e.g. aa:bb:cc:dd:ee:ff).

    \b
    Example:
      netcupctl firewall restore 12345 aa:bb:cc:dd:ee:ff
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


@firewall.command("cleanup")
@click.option("--dry-run", is_flag=True, help="List orphaned policies without deleting them.")
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_obj
def cleanup_firewall(ctx, dry_run: bool, yes: bool):
    """Delete user firewall policies that are not assigned to any interface.

    Traverses all servers and their interfaces to collect every policy ID that
    is currently in use. Any user policy not referenced by at least one interface
    is considered orphaned and can be deleted.

    Use --dry-run to preview what would be deleted without making any changes.
    This command does not delete policies that are referenced as copied policies
    on any interface, because another user may depend on them.

    \b
    Examples:
      netcupctl firewall cleanup --dry-run
      netcupctl firewall cleanup --yes
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        all_policies = _collect_all_policies(ctx, user_id)
        referenced_ids = _collect_referenced_ids(ctx)
        orphaned = {k: v for k, v in all_policies.items() if k not in referenced_ids}
        _delete_policies(ctx, user_id, orphaned, dry_run, yes)
    except click.Abort:
        click.echo("Aborted.", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
