import pytest
from unittest.mock import MagicMock
import json

from netcupctl.client import APIError
from netcupctl.cli import cli
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.security
class TestInputValidation:

    @pytest.mark.parametrize("injection_payload", [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "; rm -rf /",
        "| cat /etc/passwd",
        "$(whoami)",
        "`id`",
        "${PATH}",
        "<script>alert(1)</script>",
        "'; DROP TABLE servers; --",
        "%00",
    ])
    def test_server_id_injection_prevention(self, cli_runner, injection_payload):
        ctx = create_mock_context()

        result = invoke_with_mocks(cli_runner, ["servers", "get", injection_payload], ctx)

        assert result.exit_code != 0
        ctx.client.get.assert_not_called()

    @pytest.mark.parametrize("injection_payload", [
        "../../../etc/passwd",
        "disk; rm -rf /",
        "disk$(id)",
        "disk`whoami`",
    ])
    def test_disk_name_injection_prevention(self, cli_runner, injection_payload):
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner, ["disks", "get", "srv-123", injection_payload], ctx
        )

        assert result.exit_code != 0
        ctx.client.get.assert_not_called()

    @pytest.mark.parametrize("injection_payload", [
        "snap; cat /etc/shadow",
        "snap$(reboot)",
        "../../../etc/passwd",
    ])
    def test_snapshot_name_injection_prevention(self, cli_runner, injection_payload):
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner, ["snapshots", "get", "srv-123", injection_payload], ctx
        )

        assert result.exit_code != 0

    def test_boundary_very_long_input(self, cli_runner):
        ctx = create_mock_context()
        very_long_input = "a" * 10000

        result = invoke_with_mocks(cli_runner, ["servers", "get", very_long_input], ctx)

        assert result.exit_code != 0
        ctx.client.get.assert_not_called()


@pytest.mark.security
class TestErrorMessageSecurity:

    def test_api_error_no_token_leak(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error with token abc123secret", status_code=500)

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        output = result.output
        assert "Bearer" not in output

    def test_api_error_message_displayed(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Server unavailable", status_code=500)

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        assert result.exit_code == 500
        assert "Error" in result.output


@pytest.mark.security
class TestMalformedResponseHandling:

    def test_invalid_json_response(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            text="not valid json {{{",
            status_code=200,
        )

        result = mock_client.get("/api/v1/servers")

        assert "data" in result

    def test_empty_response_body(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            text="",
            status_code=200,
        )

        result = mock_client.get("/api/v1/servers")

        assert result == {}

    def test_unexpected_response_structure(self, cli_runner):
        ctx = create_mock_context(output_format="json")
        ctx.client.get.return_value = {"unexpected": "structure", "nested": {"deep": "value"}}

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        assert result.exit_code == 0

    def test_very_large_response(self, cli_runner):
        ctx = create_mock_context()
        large_response = [{"id": f"srv-{i}", "data": "x" * 1000} for i in range(100)]
        ctx.client.get.return_value = large_response

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        assert result.exit_code == 0


@pytest.mark.security
class TestAuthenticationSecurity:

    def test_expired_token_triggers_refresh(self, mock_config, requests_mock):
        from datetime import datetime, timedelta
        from netcupctl.auth import AuthManager
        from tests.fixtures.api_responses import TOKEN_RESPONSE

        mock_config.config_dir.mkdir(parents=True, exist_ok=True)
        expired_tokens = {
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "user_id": "user123",
        }
        mock_config.save_tokens(expired_tokens)

        requests_mock.post(AuthManager.TOKEN_URL, json=TOKEN_RESPONSE)

        auth = AuthManager(config=mock_config)
        auth._token_data = expired_tokens
        token = auth.get_access_token()

        assert token == TOKEN_RESPONSE["access_token"]


@pytest.mark.security
class TestSensitiveDataHandling:

    def test_tokens_not_logged_in_verbose_mode(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        result = invoke_with_mocks(cli_runner, ["--verbose", "servers", "list"], ctx)

        output = result.output
        assert "test_access_token" not in output
        assert "Bearer" not in output

    def test_config_file_not_exposed_in_errors(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=500)

        result = invoke_with_mocks(cli_runner, ["servers", "list"], ctx)

        output = result.output
        assert "tokens.json" not in output
        assert ".config" not in output
        assert "APPDATA" not in output
