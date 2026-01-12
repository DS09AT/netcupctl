"""
Tests for netcupctl.commands.ssh_keys
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    SSH_KEY_LIST_RESPONSE,
    SSH_KEY_DETAIL_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestSSHKeysCommands:
    """Test suite for SSH key management commands"""

    # list_keys tests
    def test_list_keys_success(self, cli_runner):
        """Test list SSH keys successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = SSH_KEY_LIST_RESPONSE

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["ssh-keys", "list"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123/ssh-keys")

    def test_list_keys_empty_list(self, cli_runner):
        """Test list SSH keys with empty result"""
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["ssh-keys", "list"], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_list_keys_api_errors(self, cli_runner, status_code):
        """Test list keys handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["ssh-keys", "list"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # add_key tests
    def test_add_key_with_key_string(self, cli_runner):
        """Test add SSH key with --key string"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SSH_KEY_DETAIL_RESPONSE

        public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host"

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "add", "--name", "my-laptop", "--key", public_key],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "SSH key added" in result.output
        ctx.client.post.assert_called_once()
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/users/user_123/ssh-keys"
        assert call_args[1]["json"]["name"] == "my-laptop"
        assert call_args[1]["json"]["key"] == public_key

    def test_add_key_with_key_file(self, cli_runner, tmp_path):
        """Test add SSH key with --key-file"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SSH_KEY_DETAIL_RESPONSE

        public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host"
        key_file = tmp_path / "id_rsa.pub"
        key_file.write_text(public_key)

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "add", "--name", "my-laptop", "--key-file", str(key_file)],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["key"] == public_key

    def test_add_key_strips_whitespace(self, cli_runner):
        """Test add key strips whitespace from key"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SSH_KEY_DETAIL_RESPONSE

        public_key_with_whitespace = "  ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host  \n"
        expected_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host"

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "add", "--name", "test", "--key", public_key_with_whitespace],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["key"] == expected_key

    def test_add_key_missing_both_options(self, cli_runner):
        """Test add key without --key or --key-file fails"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "add", "--name", "test"],
                ctx
            )

        assert result.exit_code != 0
        assert "Provide --key or --key-file" in result.output
        ctx.client.post.assert_not_called()

    def test_add_key_missing_name(self, cli_runner):
        """Test add key requires --name option"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "add", "--key", "ssh-rsa AAA..."],
                ctx
            )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_add_key_api_errors(self, cli_runner, status_code):
        """Test add key handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "add", "--name", "test", "--key", "ssh-rsa AAA..."],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # delete_key tests
    def test_delete_key_with_confirmation(self, cli_runner):
        """Test delete SSH key with confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "delete", "key-001"],
                ctx,
                input="y\n"
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "SSH key deleted" in result.output
        ctx.client.delete.assert_called_once_with("/api/v1/users/user_123/ssh-keys/key-001")

    def test_delete_key_abort(self, cli_runner):
        """Test delete SSH key abort on confirmation"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "delete", "key-001"],
                ctx,
                input="n\n"
            )

        assert result.exit_code == 1
        assert "Aborted" in result.output
        ctx.client.delete.assert_not_called()

    def test_delete_key_with_yes_flag(self, cli_runner):
        """Test delete SSH key with --yes flag skips confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "delete", "key-001", "--yes"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    def test_delete_key_with_confirm_flag(self, cli_runner):
        """Test delete SSH key with --confirm flag skips prompt"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "delete", "key-001", "--confirm"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_delete_key_api_errors(self, cli_runner, status_code):
        """Test delete key handles API errors"""
        ctx = create_mock_context()
        ctx.client.delete.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.ssh_keys.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["ssh-keys", "delete", "key-001", "--yes"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output
