"""User management commands."""

import json
import sys

import click

from netcupctl.client import APIError
from netcupctl.commands.helpers import get_authenticated_user_id


@click.group()
def users():
    """User management commands.

    View and update user profile settings.
    """
    pass


@users.command("get")
@click.pass_obj
def get_user(ctx):
    """Get your user profile.

    Displays the profile information for the authenticated user.
    """
    try:
        user_id = get_authenticated_user_id(ctx)
        result = ctx.client.get(f"/api/v1/users/{user_id}")
        ctx.formatter.output(result)
    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


@users.command("update")
@click.option("--language", type=click.Choice(["en", "de"]), help="Interface language (en or de)")
@click.option("--timezone", help="IANA timezone (e.g., Europe/Berlin, America/New_York)")
@click.option("--api-ip-restrictions", help="Comma-separated IPs/CIDRs for API access")
@click.option("--show-nickname/--hide-nickname", default=None, help="Display nickname in UI")
@click.option(
    "--enable-passwordless-mode/--disable-passwordless-mode",
    default=None,
    help="Allow passwordless authentication"
)
@click.option(
    "--enable-secure-mode/--disable-secure-mode",
    default=None,
    help="Require two-factor authentication"
)
@click.option(
    "--enable-secure-mode-app/--disable-secure-mode-app",
    default=None,
    help="Enable secure mode for app access"
)
@click.option("--password", is_flag=True, help="Change password (prompts securely)")
@click.option("--interactive", is_flag=True, help="Guided interactive mode")
@click.option("--json", "json_data", help="JSON string for scripting (e.g., '{\"language\": \"de\"}')")
@click.option("--data", hidden=True, help="[DEPRECATED] Use --json instead")
@click.pass_obj
def update_user(ctx, language, timezone, api_ip_restrictions, show_nickname,
                enable_passwordless_mode, enable_secure_mode, enable_secure_mode_app,
                password, interactive, json_data, data):
    """Update your user profile.

    \b
    Examples:
      # Update language
      netcupctl users update --language de

      # Update timezone
      netcupctl users update --timezone "Europe/Berlin"

      # Multiple fields
      netcupctl users update --language en --timezone "America/New_York"

      # Change password securely
      netcupctl users update --password

      # Interactive mode
      netcupctl users update --interactive

      # JSON mode (for scripting)
      netcupctl users update --json '{"language": "de", "timeZone": "UTC"}'
    """
    try:
        user_id = get_authenticated_user_id(ctx)

        if data:
            click.echo(
                "Warning: --data is deprecated and will be removed in v3.0. "
                "Use --json instead.",
                err=True
            )
            json_data = data

        if json_data:
            if any([language, timezone, api_ip_restrictions, show_nickname is not None,
                    enable_passwordless_mode is not None, enable_secure_mode is not None,
                    enable_secure_mode_app is not None, password, interactive]):
                click.echo("Error: Cannot use --json with other options.", err=True)
                sys.exit(2)

            try:
                user_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                click.echo(f"Error: Invalid JSON - {e}", err=True)
                sys.exit(1)

            result = ctx.client.put(f"/api/v1/users/{user_id}", json=user_data)
            ctx.formatter.output(result)
            click.echo("\n[OK] User profile updated.", err=False)
            return

        if interactive:
            if any([language, timezone, api_ip_restrictions, show_nickname is not None,
                    enable_passwordless_mode is not None, enable_secure_mode is not None,
                    enable_secure_mode_app is not None, password]):
                click.echo("Error: Cannot use --interactive with other options.", err=True)
                sys.exit(2)

            _update_interactive(ctx, user_id)
            return

        if not any([language, timezone, api_ip_restrictions, show_nickname is not None,
                    enable_passwordless_mode is not None, enable_secure_mode is not None,
                    enable_secure_mode_app is not None, password]):
            click.echo("Error: No updates specified. Use --help for available options.", err=True)
            sys.exit(1)

        current_data = ctx.client.get(f"/api/v1/users/{user_id}")

        update_data = {
            "id": current_data.get("id"),
            "language": current_data.get("language", "en"),
            "timeZone": current_data.get("timeZone") or "UTC",
        }

        if language:
            update_data["language"] = language
        if timezone:
            update_data["timeZone"] = timezone
        if api_ip_restrictions is not None:
            update_data["apiIpLoginRestrictions"] = api_ip_restrictions
        if show_nickname is not None:
            update_data["showNickname"] = show_nickname
        if enable_passwordless_mode is not None:
            update_data["passwordlessMode"] = enable_passwordless_mode
        if enable_secure_mode is not None:
            update_data["secureMode"] = enable_secure_mode
        if enable_secure_mode_app is not None:
            update_data["secureModeAppAccess"] = enable_secure_mode_app

        if password:
            old_password = click.prompt("Current password", hide_input=True)
            new_password = click.prompt("New password", hide_input=True)
            confirm_password = click.prompt("Confirm new password", hide_input=True)

            if new_password != confirm_password:
                click.echo("Error: Passwords do not match.", err=True)
                sys.exit(1)

            update_data["oldPassword"] = old_password
            update_data["password"] = new_password

        result = ctx.client.put(f"/api/v1/users/{user_id}", json=update_data)
        ctx.formatter.output(result)
        click.echo("\n[OK] User profile updated.", err=False)

    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)


def _update_interactive(ctx, user_id):
    """Interactive mode for user updates."""
    try:
        current_data = ctx.client.get(f"/api/v1/users/{user_id}")

        click.echo("Current profile settings:")
        language = current_data.get("language", "not set")
        timezone = current_data.get("timeZone", "not set")
        show_nick = current_data.get("showNickname", False)
        pwdless = current_data.get("passwordlessMode", False)
        secure = current_data.get("secureMode", False)
        secure_app = current_data.get("secureModeAppAccess", False)
        api_restrictions = current_data.get("apiIpLoginRestrictions", "none")

        click.echo(f"  Language: {language}")
        click.echo(f"  Timezone: {timezone}")
        click.echo(f"  Show nickname: {show_nick}")
        click.echo(f"  Passwordless mode: {pwdless}")
        click.echo(f"  Secure mode: {secure}")
        click.echo(f"  Secure mode (app): {secure_app}")
        click.echo(f"  API IP restrictions: {api_restrictions}")
        click.echo()

        update_data = {
            "id": current_data.get("id"),
            "language": click.prompt(
                "Language (en/de)",
                default=current_data.get("language", "en"),
                type=click.Choice(["en", "de"])
            ),
            "timeZone": click.prompt(
                "Timezone (IANA format)",
                default=current_data.get("timeZone", "UTC")
            ),
        }

        api_ip_restrictions = click.prompt(
            "API IP restrictions (leave empty for none)",
            default=current_data.get("apiIpLoginRestrictions") or "",
            show_default=False
        )
        if api_ip_restrictions.strip():
            update_data["apiIpLoginRestrictions"] = api_ip_restrictions

        update_data["showNickname"] = click.confirm(
            "Show nickname?",
            default=current_data.get("showNickname", False)
        )
        update_data["passwordlessMode"] = click.confirm(
            "Enable passwordless mode?",
            default=current_data.get("passwordlessMode", False)
        )
        update_data["secureMode"] = click.confirm(
            "Enable secure mode?",
            default=current_data.get("secureMode", False)
        )
        update_data["secureModeAppAccess"] = click.confirm(
            "Enable secure mode for app access?",
            default=current_data.get("secureModeAppAccess", False)
        )

        if click.confirm("Change password?", default=False):
            old_password = click.prompt("Current password", hide_input=True)
            new_password = click.prompt("New password", hide_input=True)
            confirm_password = click.prompt("Confirm new password", hide_input=True)

            if new_password != confirm_password:
                click.echo("Error: Passwords do not match.", err=True)
                sys.exit(1)

            update_data["oldPassword"] = old_password
            update_data["password"] = new_password

        result = ctx.client.put(f"/api/v1/users/{user_id}", json=update_data)
        ctx.formatter.output(result)
        click.echo("\n[OK] User profile updated.", err=False)

    except APIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.status_code or 1)
