"""Main CLI module for netcupctl."""

import ssl
import sys
import warnings
from datetime import datetime

# urllib3 v2 emits a misleading warning on LibreSSL (macOS system Python) even though
# standard HTTPS works. The filter must come before any import that loads urllib3.
if "LibreSSL" in ssl.OPENSSL_VERSION:
    warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

from typing import Optional

import click

from netcupctl import __version__
from netcupctl.auth import AuthError, AuthManager
from netcupctl.client import APIError, NetcupClient
from netcupctl.config import ConfigManager
from netcupctl.output import OutputFormatter
from netcupctl.commands.custom_images import custom_images
from netcupctl.commands.custom_isos import custom_isos
from netcupctl.commands.disks import disks
from netcupctl.commands.failover_ips import failover_ips
from netcupctl.commands.firewall import firewall
from netcupctl.commands.firewall_policies import firewall_policies
from netcupctl.commands.guest_agent import guest_agent
from netcupctl.commands.images import images
from netcupctl.commands.interfaces import interfaces
from netcupctl.commands.iso import iso
from netcupctl.commands.logs import logs
from netcupctl.commands.maintenance import maintenance
from netcupctl.commands.metrics import metrics
from netcupctl.commands.rdns import rdns
from netcupctl.commands.rescue import rescue
from netcupctl.commands.servers import servers
from netcupctl.commands.snapshots import snapshots
from netcupctl.commands.spec import spec
from netcupctl.commands.ssh_keys import ssh_keys
from netcupctl.commands.storage import storage
from netcupctl.commands.tasks import tasks
from netcupctl.commands.user_logs import user_logs
from netcupctl.commands.users import users
from netcupctl.commands.vlans import vlans


class Context:
    """CLI context object shared between commands."""

    def __init__(self):
        """Initialize context."""
        self.config = ConfigManager()
        self.auth = AuthManager(self.config)
        self.client: Optional[NetcupClient] = None
        self.formatter: Optional[OutputFormatter] = None
        self.verbose: bool = False


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option(
    "--format",
    type=click.Choice(["json", "yaml", "table", "list"], case_sensitive=False),
    default="list",
    help="Output format (default: list)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.version_option(version=__version__, prog_name="netcupctl")
@click.pass_context
def cli(ctx, format: str, verbose: bool):
    """netcupctl - CLI client for netcup Server Control Panel REST API.

    Manage your netcup vServers and root servers from the command line.
    """
    # Initialize context
    context = Context()
    context.formatter = OutputFormatter(format=format.lower())
    context.verbose = verbose

    commands_without_client = ("auth", "spec")
    if ctx.invoked_subcommand not in commands_without_client:
        context.client = NetcupClient(context.auth, verbose=verbose)

    ctx.obj = context


@cli.group()
@pass_context
def auth(ctx):
    """Authentication commands."""
    pass


@auth.command()
@pass_context
def login(ctx):
    """Login using OAuth2 Device Flow.

    Opens your browser for authentication. After successful login,
    tokens are stored locally for future use.
    """
    try:
        tokens = ctx.auth.login()
        click.echo("\n[OK] Successfully logged in!")
        click.echo(f"User ID: {tokens.get('user_id', 'unknown')}")  # pylint: disable=inconsistent-quotes
        click.echo(f"Token expires: {tokens.get('expires_at', 'unknown')}")  # pylint: disable=inconsistent-quotes
    except AuthError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@auth.command()
@pass_context
def logout(ctx):
    """Logout and delete stored tokens.

    Revokes the refresh token at the server and removes local token storage.
    """
    try:
        if ctx.auth.logout():
            click.echo("[OK] Successfully logged out.")
        else:
            click.echo("Not logged in.")
    except AuthError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@auth.command("ensure")
@click.option(
    "--min-ttl",
    type=int,
    default=300,
    help="Minimum required token lifetime in seconds (default: 300).",
)
@pass_context
def auth_ensure(ctx, min_ttl: int):
    """Ensure the session token is valid and will remain so for at least MIN_TTL seconds.

    This command is safe to call at the top of any shell script to pre-validate
    and, if necessary, silently refresh the token before a long-running operation.
    It does not trigger a browser-based login flow; if the session has expired
    entirely the command exits with an error and asks the user to run 'auth login'.

    The command prints the remaining token lifetime to stdout and exits 0 on
    success, or exits 1 if the session is missing or cannot be refreshed.

    \b
    Examples:
      netcupctl auth ensure
      netcupctl auth ensure --min-ttl 600
    """
    if not ctx.auth.is_authenticated():
        click.echo("Error: Not authenticated. Run 'netcupctl auth login' first.", err=True)
        sys.exit(1)

    info = ctx.auth.get_token_info()
    expires_at = datetime.fromisoformat(info["expires_at"])
    ttl = int((expires_at - datetime.now()).total_seconds())

    if ttl < min_ttl:
        ctx.auth.get_access_token()
        info = ctx.auth.get_token_info()
        expires_at = datetime.fromisoformat(info["expires_at"])
        ttl = int((expires_at - datetime.now()).total_seconds())

    click.echo(f"[OK] Token valid for {ttl}s.")


@auth.command()
@pass_context
def status(ctx):
    """Show authentication status.

    Displays information about the current login session,
    including user ID and token expiry time.
    """
    try:
        if ctx.auth.is_authenticated():
            info = ctx.auth.get_token_info()
            if info:
                click.echo(f"Logged in as: {info['user_id']}")  # pylint: disable=inconsistent-quotes
                click.echo(f"Token valid until: {info['expires_at']}")  # pylint: disable=inconsistent-quotes
        else:
            click.echo("Not logged in.")
            click.echo("\nRun 'netcupctl auth login' to authenticate.")
    except AuthError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def ping(ctx):
    """Check if the API is available.

    Performs a simple health check against the API.
    """
    try:
        # The ping endpoint returns plain text only, so the default JSON Accept header causes a 400 error.
        result = ctx.client.get("/api/ping", accept="text/plain, */*")
        if isinstance(result, dict) and "data" in result:
            click.echo(result["data"])
        else:
            click.echo("OK")
    except APIError as e:
        click.echo(f"API unavailable: {e}", err=True)
        sys.exit(e.status_code or 1)


cli.add_command(custom_images)
cli.add_command(custom_isos)
cli.add_command(disks)
cli.add_command(failover_ips)
cli.add_command(firewall)
cli.add_command(firewall_policies)
cli.add_command(guest_agent)
cli.add_command(images)
cli.add_command(interfaces)
cli.add_command(iso)
cli.add_command(logs)
cli.add_command(maintenance)
cli.add_command(metrics)
cli.add_command(rdns)
cli.add_command(rescue)
cli.add_command(servers)
cli.add_command(servers, name="server")
cli.add_command(snapshots)
cli.add_command(spec)
cli.add_command(ssh_keys)
cli.add_command(storage)
cli.add_command(tasks)
cli.add_command(user_logs)
cli.add_command(users)
cli.add_command(vlans)


def main():
    """Main entry point for CLI."""
    try:
        cli()  # pylint: disable=no-value-for-parameter
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user.", err=True)
        sys.exit(130)
    except (AuthError, APIError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
