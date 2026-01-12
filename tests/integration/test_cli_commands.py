import pytest
from click.testing import CliRunner

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks
from tests.fixtures.api_responses import (
    SERVER_LIST_RESPONSE,
    DISK_LIST_RESPONSE,
    SNAPSHOT_LIST_RESPONSE,
    SSH_KEY_LIST_RESPONSE,
    VLAN_LIST_RESPONSE,
    INTERFACE_LIST_RESPONSE,
)


@pytest.mark.integration
class TestCliCommandGroups:

    @pytest.mark.parametrize("format_type", ["json", "table", "list"])
    def test_servers_list_output_formats(self, cli_runner, format_type):
        ctx = create_mock_context(output_format=format_type)
        ctx.client.get.return_value = SERVER_LIST_RESPONSE

        result = invoke_with_mocks(
            cli_runner, ["--format", format_type, "servers", "list"], ctx
        )

        assert result.exit_code == 0

    def test_servers_workflow(self, cli_runner):
        ctx = create_mock_context()

        ctx.client.get.return_value = SERVER_LIST_RESPONSE
        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)
        assert result.exit_code == 0

        ctx.client.get.return_value = SERVER_LIST_RESPONSE[0]
        result = invoke_with_mocks(cli_runner, ["servers", "get", "srv-12345"], ctx)
        assert result.exit_code == 0

        ctx.client.patch.return_value = {"state": "running"}
        result = invoke_with_mocks(cli_runner, ["servers", "start", "srv-12345"], ctx)
        assert result.exit_code == 0

        ctx.client.patch.return_value = {"state": "stopped"}
        result = invoke_with_mocks(cli_runner, ["servers", "stop", "srv-12345"], ctx)
        assert result.exit_code == 0

    def test_disks_workflow(self, cli_runner):
        ctx = create_mock_context()

        ctx.client.get.return_value = DISK_LIST_RESPONSE
        result = invoke_with_mocks(cli_runner, ["disks", "list", "srv-12345"], ctx)
        assert result.exit_code == 0

        ctx.client.get.return_value = DISK_LIST_RESPONSE[0]
        result = invoke_with_mocks(
            cli_runner, ["disks", "get", "srv-12345", "system-disk"], ctx
        )
        assert result.exit_code == 0

    def test_snapshots_workflow(self, cli_runner):
        ctx = create_mock_context()

        ctx.client.get.return_value = SNAPSHOT_LIST_RESPONSE
        result = invoke_with_mocks(cli_runner, ["snapshots", "list", "srv-12345"], ctx)
        assert result.exit_code == 0

    def test_ssh_keys_workflow(self, cli_runner):
        ctx = create_mock_context()

        ctx.client.get.return_value = SSH_KEY_LIST_RESPONSE
        result = invoke_with_mocks(cli_runner, ["ssh-keys", "list"], ctx)
        assert result.exit_code == 0

    def test_vlans_workflow(self, cli_runner):
        ctx = create_mock_context()

        ctx.client.get.return_value = VLAN_LIST_RESPONSE
        result = invoke_with_mocks(cli_runner, ["vlans", "list"], ctx)
        assert result.exit_code == 0

    def test_interfaces_workflow(self, cli_runner):
        ctx = create_mock_context()

        ctx.client.get.return_value = INTERFACE_LIST_RESPONSE
        result = invoke_with_mocks(cli_runner, ["interfaces", "list", "srv-12345"], ctx)
        assert result.exit_code == 0


@pytest.mark.integration
class TestCliErrorHandling:

    def test_api_error_shows_message(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Resource not found", status_code=404)

        result = invoke_with_mocks(cli_runner, ["servers", "get", "nonexistent"], ctx)

        assert result.exit_code == 404

    def test_server_error_shows_generic_message(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Internal server error", status_code=500)

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        assert result.exit_code == 500


@pytest.mark.integration
class TestCliMixedOptions:

    def test_global_and_command_options(self, cli_runner):
        ctx = create_mock_context(output_format="json")
        ctx.client.get.return_value = SERVER_LIST_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["--format", "json", "--verbose", "servers", "list", "--limit", "10"],
            ctx,
        )

        assert result.exit_code == 0

    def test_json_output_is_valid(self, cli_runner):
        import json
        ctx = create_mock_context(output_format="json")
        ctx.client.get.return_value = SERVER_LIST_RESPONSE

        result = invoke_with_mocks(
            cli_runner, ["--format", "json", "servers", "list"], ctx
        )

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
