import pytest
from unittest.mock import MagicMock
from click.testing import CliRunner

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import SERVER_LIST_RESPONSE, SERVER_DETAIL_RESPONSE
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestServersCommands:

    def test_list_servers_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = SERVER_LIST_RESPONSE

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once()

    def test_list_servers_with_limit(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = SERVER_LIST_RESPONSE

        result = invoke_with_mocks(cli_runner, ["servers", "list", "--limit", "50"], ctx)

        assert result.exit_code == 0
        call_args = ctx.client.get.call_args
        assert call_args[1]["params"]["limit"] == 50

    def test_list_servers_api_error(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Server error", status_code=500)

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        assert result.exit_code == 500

    def test_get_server_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = SERVER_DETAIL_RESPONSE

        result = invoke_with_mocks(cli_runner, ["servers", "get", "srv-12345"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once()

    def test_get_server_invalid_id(self, cli_runner):
        ctx = create_mock_context()

        result = invoke_with_mocks(cli_runner, ["servers", "get", "../../../etc/passwd"], ctx)

        assert result.exit_code != 0

    def test_get_server_not_found(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Not found", status_code=404)

        result = invoke_with_mocks(cli_runner, ["servers", "get", "nonexistent"], ctx)

        assert result.exit_code == 404

    def test_start_server_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.patch.return_value = {"id": "srv-12345", "state": "running"}

        result = invoke_with_mocks(cli_runner, ["servers", "start", "srv-12345"], ctx)

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.patch.assert_called_once()
        call_args = ctx.client.patch.call_args
        assert call_args[1]["json"]["state"] == "ON"

    def test_stop_server_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.patch.return_value = {"id": "srv-12345", "state": "stopped"}

        result = invoke_with_mocks(cli_runner, ["servers", "stop", "srv-12345"], ctx)

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.patch.call_args
        assert call_args[1]["json"]["state"] == "OFF"

    def test_reboot_server_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.patch.return_value = {"id": "srv-12345", "state": "reboot"}

        result = invoke_with_mocks(cli_runner, ["servers", "reboot", "srv-12345"], ctx)

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.patch.call_args
        assert call_args[1]["json"]["state"] == "ON"
        assert call_args[1]["params"]["stateOption"] == "RESET"

    def test_server_action_unauthorized(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.patch.side_effect = APIError("Unauthorized", status_code=401)

        result = invoke_with_mocks(cli_runner, ["servers", "start", "srv-12345"], ctx)

        assert result.exit_code == 401

    @pytest.mark.parametrize("server_id", [
        "valid-server-123",
        "server_with_underscore",
        "SERVER123",
    ])
    def test_valid_server_ids(self, cli_runner, server_id):
        ctx = create_mock_context()
        ctx.client.get.return_value = SERVER_DETAIL_RESPONSE

        result = invoke_with_mocks(cli_runner, ["servers", "get", server_id], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("server_id", [
        "server/with/slashes",
        "server;injection",
        "server$(cmd)",
        "a" * 100,
    ])
    def test_invalid_server_ids(self, cli_runner, server_id):
        ctx = create_mock_context()

        result = invoke_with_mocks(cli_runner, ["servers", "get", server_id], ctx)

        assert result.exit_code != 0
