"""Shared helper functions for CLI commands."""

import sys

import click

from netcupctl.client import APIError


def get_authenticated_user_id(ctx) -> str:
    """Get the authenticated user's ID from token info.

    Args:
        ctx: Click context object with auth manager

    Returns:
        User ID string

    Exits:
        If not authenticated or user ID unavailable
    """
    info = ctx.auth.get_token_info()
    if not info or "user_id" not in info:
        click.echo("Error: Not authenticated. Run 'netcupctl auth login' first.", err=True)
        sys.exit(1)
    return info["user_id"]


def upsert_policy(ctx, user_id: str, name: str, rules_data: dict) -> int:
    """Create or update a firewall policy identified by exact name.

    Searches for an existing policy with the given name. If exactly one match
    is found it is updated in place; if none exist a new policy is created.
    The function raises APIError when multiple policies share the same name,
    since it is impossible to determine which one to update safely.

    Args:
        ctx: CLI context with an authenticated client.
        user_id: The authenticated user's ID.
        name: Exact policy name to match.
        rules_data: Dict merged into the policy body alongside the name field.

    Returns:
        Integer policy ID of the created or updated policy.

    Raises:
        APIError: On API failure or when multiple policies share the given name.
    """
    result = ctx.client.get(
        f"/api/v1/users/{user_id}/firewall-policies",
        params={"q": name, "limit": 100},
    )
    policies = result if isinstance(result, list) else []
    exact = [p for p in policies if p.get("name") == name]

    if len(exact) > 1:
        raise APIError(
            f"Multiple policies named '{name}' exist. "
            "Delete duplicates before proceeding."
        )

    if len(exact) == 1:
        policy_id = exact[0]["id"]
        ctx.client.put(
            f"/api/v1/users/{user_id}/firewall-policies/{policy_id}",
            json={"name": name, **rules_data},
        )
        return policy_id

    response = ctx.client.post(
        f"/api/v1/users/{user_id}/firewall-policies",
        json={"name": name, **rules_data},
    )
    return response["id"]
