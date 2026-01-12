import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from netcupctl.cli import cli
from netcupctl.auth import AuthError
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.integration
class TestCliAuth:

    def test_auth_help(self, cli_runner):
        result = cli_runner.invoke(cli, ["auth", "--help"])

        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output

    def test_auth_status_authenticated(self, cli_runner):
        ctx = create_mock_context(
            authenticated=True,
            token_data={
                "user_id": "test_user_123",
                "expires_at": "2099-12-31T23:59:59",
            },
        )

        result = invoke_with_mocks(cli_runner, ["auth", "status"], ctx)

        assert result.exit_code == 0
        assert "test_user_123" in result.output

    def test_auth_status_not_authenticated(self, cli_runner):
        ctx = create_mock_context(authenticated=False)

        result = invoke_with_mocks(cli_runner, ["auth", "status"], ctx)

        assert result.exit_code == 0
        assert "Not logged in" in result.output

    def test_auth_logout_success(self, cli_runner):
        ctx = create_mock_context(authenticated=True)
        ctx.auth.logout.return_value = True

        result = invoke_with_mocks(cli_runner, ["auth", "logout"], ctx)

        assert result.exit_code == 0
        assert "[OK]" in result.output or "logged out" in result.output.lower()

    def test_auth_logout_not_logged_in(self, cli_runner):
        ctx = create_mock_context(authenticated=False)
        ctx.auth.logout.return_value = False

        result = invoke_with_mocks(cli_runner, ["auth", "logout"], ctx)

        assert result.exit_code == 0
        assert "Not logged in" in result.output

    def test_auth_logout_error(self, cli_runner):
        ctx = create_mock_context(authenticated=True)
        ctx.auth.logout.side_effect = AuthError("Failed to revoke token")

        result = invoke_with_mocks(cli_runner, ["auth", "logout"], ctx)

        assert result.exit_code != 0

    def test_auth_status_error(self, cli_runner):
        ctx = create_mock_context(authenticated=True)
        ctx.auth.is_authenticated.side_effect = AuthError("Token corrupted")

        result = invoke_with_mocks(cli_runner, ["auth", "status"], ctx)

        assert result.exit_code != 0


@pytest.mark.integration
class TestCliAuthLogin:

    def test_login_help(self, cli_runner):
        result = cli_runner.invoke(cli, ["auth", "login", "--help"])

        assert result.exit_code == 0
        assert "OAuth2" in result.output or "login" in result.output.lower()
