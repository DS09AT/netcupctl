"""Main CLI module for netcupctl."""

import sys
from typing import Optional

import click

from netcupctl import __version__
from netcupctl.auth import AuthManager
from netcupctl.client import NetcupClient
from netcupctl.config import ConfigManager
from netcupctl.output import OutputFormatter
from netcupctl.commands.servers import servers
from netcupctl.commands.spec import spec


class Context:
    """CLI context object shared between commands."""

    def __init__(self):
        """Initialize context."""
        self.config = ConfigManager()
        self.auth = AuthManager(self.config)
        self.client: Optional[NetcupClient] = None
        self.formatter: Optional[OutputFormatter] = None


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option(
    "--format",
    type=click.Choice(["json", "table"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
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

    # Only initialize client if command needs it
    if ctx.invoked_subcommand not in ("auth", "spec"):
        context.client = NetcupClient(context.auth)

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
        click.echo(f"\n[OK] Successfully logged in!")
        click.echo(f"User ID: {tokens.get('user_id', 'unknown')}")
        click.echo(f"Token expires: {tokens.get('expires_at', 'unknown')}")
    except Exception as e:
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
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


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
                click.echo(f"Logged in as: {info['user_id']}")
                click.echo(f"Token valid until: {info['expires_at']}")
        else:
            click.echo("Not logged in.")
            click.echo("\nRun 'netcupctl auth login' to authenticate.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Register command groups
cli.add_command(servers)
cli.add_command(spec)


def main():
    """Main entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user.", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
