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

    # get_user tests
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

    # update_user tests
    def test_update_user_success(self, cli_runner):
        """Test update user profile successfully"""
        ctx = create_mock_context()
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        user_data = '{"email": "updated@example.com"}'

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--data", user_data],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "User profile updated" in result.output
        ctx.client.put.assert_called_once()
        call_args = ctx.client.put.call_args
        assert call_args[0][0] == "/api/v1/users/user_123"
        assert call_args[1]["json"] == {"email": "updated@example.com"}

    def test_update_user_invalid_json(self, cli_runner):
        """Test update user with invalid JSON"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--data", "invalid json"],
                ctx
            )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output
        ctx.client.put.assert_not_called()

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_update_user_api_errors(self, cli_runner, status_code):
        """Test update user handles API errors"""
        ctx = create_mock_context()
        ctx.client.put.side_effect = APIError("Error", status_code=status_code)

        user_data = '{"email": "test@example.com"}'

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--data", user_data],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    def test_update_user_missing_data_option(self, cli_runner):
        """Test update user requires --data option"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["users", "update"], ctx)

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_update_user_with_complex_data(self, cli_runner):
        """Test update user with complex JSON data"""
        ctx = create_mock_context()
        ctx.client.put.return_value = USER_UPDATE_RESPONSE

        user_data = '{"email": "new@example.com", "preferred_username": "newuser", "email_verified": true}'

        with patch("netcupctl.commands.users.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["users", "update", "--data", user_data],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["email"] == "new@example.com"
        assert call_args[1]["json"]["preferred_username"] == "newuser"
        assert call_args[1]["json"]["email_verified"] is True
