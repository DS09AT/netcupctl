"""
Tests for netcupctl.commands.users
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    USERINFO_RESPONSE,
    USER_UPDATE_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestUsersCommands:
    """Test suite for user management commands"""

    def test_get_user_success(self, cli_runner):
        """Test get user profile successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = USERINFO_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["users", "get"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123")

    @pytest.mark.parametrize("status_code,error_response", [
        (401, ERROR_RESPONSE_401),
        (404, ERROR_RESPONSE_404),
        (500, ERROR_RESPONSE_500),
    ])
    def test_get_user_api_errors(self, cli_runner, status_code, error_response):
        """Test get user handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["users", "get"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    def test_update_user_with_language_option(self, cli_runner):
        """Test update user with --language option"""
        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "en",
            "timeZone": "America/New_York"
        }
        ctx.client.get.return_value = current_user_data
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--language", "de"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123")
        call_args = ctx.client.put.call_args
        assert call_args[0][0] == "/api/v1/users/user_123"
        assert call_args[1]["json"]["language"] == "de"
        assert call_args[1]["json"]["timeZone"] == "America/New_York"

    def test_update_user_with_timezone_option(self, cli_runner):
        """Test update user with --timezone option"""
        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "en",
            "timeZone": "America/New_York"
        }
        ctx.client.get.return_value = current_user_data
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--timezone", "Europe/Berlin"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["language"] == "en"
        assert call_args[1]["json"]["timeZone"] == "Europe/Berlin"

    def test_update_user_with_multiple_options(self, cli_runner):
        """Test update user with multiple options"""
        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "de",
            "timeZone": "Europe/Berlin"
        }
        ctx.client.get.return_value = current_user_data
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--language", "en", "--timezone", "America/New_York", "--api-ip-restrictions", "203.0.113.0/24"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["language"] == "en"
        assert call_args[1]["json"]["timeZone"] == "America/New_York"
        assert call_args[1]["json"]["apiIpLoginRestrictions"] == "203.0.113.0/24"

    def test_update_user_with_show_nickname(self, cli_runner):
        """Test update user with --show-nickname flag"""
        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "en",
            "timeZone": "UTC",
            "showNickname": False
        }
        ctx.client.get.return_value = current_user_data
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--show-nickname"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["showNickname"] is True

    def test_update_user_with_passwordless_mode_toggle(self, cli_runner):
        """Test update user with passwordless mode toggle"""
        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "en",
            "timeZone": "UTC",
            "passwordlessMode": False
        }
        ctx.client.get.return_value = current_user_data
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--enable-passwordless-mode"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["passwordlessMode"] is True

    def test_update_user_with_secure_mode_toggle(self, cli_runner):
        """Test update user with secure mode toggle"""
        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "en",
            "timeZone": "UTC",
            "secureMode": False
        }
        ctx.client.get.return_value = current_user_data
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--enable-secure-mode"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["secureMode"] is True

    @patch("click.prompt")
    def test_update_user_with_password(self, mock_prompt, cli_runner):
        """Test update user with password change"""
        mock_prompt.side_effect = ["oldpass123", "newpass123", "newpass123"]

        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "en",
            "timeZone": "UTC"
        }
        ctx.client.get.return_value = current_user_data
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--password"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["oldPassword"] == "oldpass123"
        assert call_args[1]["json"]["password"] == "newpass123"

    @patch("click.prompt")
    def test_update_user_password_mismatch(self, mock_prompt, cli_runner):
        """Test update user with password mismatch"""
        mock_prompt.side_effect = ["oldpass123", "newpass123", "wrongconfirm"]

        ctx = create_mock_context()
        current_user_data = {
            "id": "user_123",
            "language": "en",
            "timeZone": "UTC"
        }
        ctx.client.get.return_value = current_user_data

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--password"],
                ctx
            )

        assert result.exit_code == 1
        assert "Passwords do not match" in result.output
        ctx.client.put.assert_not_called()

    def test_update_user_json_mode(self, cli_runner):
        """Test update user with --json option"""
        ctx = create_mock_context()
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        user_data = '{"language": "de", "timeZone": "Europe/Berlin"}'

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--json", user_data],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.get.assert_not_called()
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["language"] == "de"
        assert call_args[1]["json"]["timeZone"] == "Europe/Berlin"

    def test_update_user_data_deprecated_warning(self, cli_runner):
        """Test update user with deprecated --data shows warning"""
        ctx = create_mock_context()
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        user_data = '{"language": "de", "timeZone": "UTC"}'

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--data", user_data],
                ctx
            )

        assert result.exit_code == 0
        assert "deprecated" in result.output.lower()
        assert "--json" in result.output

    def test_update_user_json_invalid(self, cli_runner):
        """Test update user with invalid JSON"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--json", "invalid json"],
                ctx
            )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output
        ctx.client.put.assert_not_called()

    def test_update_user_json_mutually_exclusive(self, cli_runner):
        """Test --json is mutually exclusive with other options"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--json", '{"language": "de"}', "--language", "en"],
                ctx
            )

        assert result.exit_code == 2
        assert "Cannot use --json with other options" in result.output

    def test_update_user_no_options_error(self, cli_runner):
        """Test update user with no options shows error"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update"],
                ctx
            )

        assert result.exit_code == 1
        assert "No updates specified" in result.output

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_update_user_api_errors(self, cli_runner, status_code):
        """Test update user handles API errors"""
        ctx = create_mock_context()
        current_user_data = {"language": "en", "timeZone": "UTC"}
        ctx.client.get.return_value = current_user_data
        ctx.client.put.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--language", "de"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output
