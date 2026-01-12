import pytest
from click.testing import CliRunner

from netcupctl.cli import cli
from netcupctl import __version__
from netcupctl.client import APIError
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.integration
class TestCliMain:

    def test_cli_help(self, cli_runner):
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "netcupctl" in result.output
        assert "Server Control Panel" in result.output

    def test_cli_version(self, cli_runner):
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    @pytest.mark.parametrize("format_option", ["json", "table", "list"])
    def test_cli_format_option(self, cli_runner, format_option):
        ctx = create_mock_context()
        ctx.client.get.return_value = [{"id": "1"}]

        result = invoke_with_mocks(
            cli_runner, ["--format", format_option, "servers", "list"], ctx
        )

        assert result.exit_code == 0

    def test_cli_invalid_format(self, cli_runner):
        result = cli_runner.invoke(cli, ["--format", "invalid", "servers", "list"])

        assert result.exit_code != 0

    def test_cli_verbose_flag(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        result = invoke_with_mocks(cli_runner, ["--verbose", "servers", "list"], ctx)

        assert result.exit_code == 0

    def test_cli_unknown_command(self, cli_runner):
        result = cli_runner.invoke(cli, ["nonexistent"])

        assert result.exit_code != 0

    def test_cli_ping_command(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = {"data": "OK"}

        result = invoke_with_mocks(cli_runner, ["ping"], ctx)

        assert result.exit_code == 0
        assert "OK" in result.output

    def test_cli_ping_api_unavailable(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Connection refused", status_code=503)

        result = invoke_with_mocks(cli_runner, ["ping"], ctx)

        assert result.exit_code == 503

    @pytest.mark.parametrize("command_group", [
        "servers",
        "disks",
        "snapshots",
        "vlans",
        "firewall",
        "ssh-keys",
        "interfaces",
    ])
    def test_command_groups_have_help(self, cli_runner, command_group):
        result = cli_runner.invoke(cli, [command_group, "--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output or "Commands:" in result.output
