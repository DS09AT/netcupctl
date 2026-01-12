"""
Tests for netcupctl.commands.images
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    IMAGE_LIST_RESPONSE,
    IMAGE_DETAIL_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestImagesCommands:
    """Test suite for image management commands"""

    # list_flavours tests
    def test_list_flavours_success(self, cli_runner):
        """Test list image flavours successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = IMAGE_LIST_RESPONSE

        result = invoke_with_mocks(cli_runner, ["images", "list", "srv-12345"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/servers/srv-12345/imageflavours")

    def test_list_flavours_empty_list(self, cli_runner):
        """Test list flavours with empty result"""
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        result = invoke_with_mocks(cli_runner, ["images", "list", "srv-12345"], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_list_flavours_api_errors(self, cli_runner, status_code):
        """Test list flavours handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(cli_runner, ["images", "list", "srv-12345"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # show_image tests
    def test_show_image_success(self, cli_runner):
        """Test show current image successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = IMAGE_DETAIL_RESPONSE

        result = invoke_with_mocks(cli_runner, ["images", "show", "srv-12345"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/servers/srv-12345/image")

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_show_image_api_errors(self, cli_runner, status_code):
        """Test show image handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(cli_runner, ["images", "show", "srv-12345"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # install_image tests
    def test_install_image_with_password_confirm(self, cli_runner):
        """Test install image with password and --confirm flag"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {"task_id": "task-001"}

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install", "srv-12345", "--flavour", "ubuntu-22.04", "--password", "SecurePass123", "--confirm"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Image installation started" in result.output
        ctx.client.post.assert_called_once()
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/image"
        assert call_args[1]["json"]["imageFlavourId"] == "ubuntu-22.04"
        assert call_args[1]["json"]["password"] == "SecurePass123"

    def test_install_image_with_all_options(self, cli_runner):
        """Test install image with all optional parameters"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {"task_id": "task-001"}

        result = invoke_with_mocks(
            cli_runner,
            [
                "images", "install", "srv-12345",
                "--flavour", "debian-12",
                "--hostname", "web-server",
                "--password", "SecurePass123",
                "--ssh-keys", "key-001,key-002",
                "--yes"
            ],
            ctx
        )

        assert result.exit_code == 0
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["hostname"] == "web-server"
        assert call_args[1]["json"]["sshKeyIds"] == ["key-001", "key-002"]

    def test_install_image_abort_confirmation(self, cli_runner):
        """Test install image abort on confirmation"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install", "srv-12345", "--flavour", "ubuntu-22.04", "--password", "pass"],
            ctx,
            input="n\n"
        )

        assert result.exit_code == 1
        assert "Aborted" in result.output
        ctx.client.post.assert_not_called()

    def test_install_image_with_confirmation_yes(self, cli_runner):
        """Test install image with user confirmation"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {"task_id": "task-001"}

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install", "srv-12345", "--flavour", "ubuntu-22.04", "--password", "pass"],
            ctx,
            input="y\n"
        )

        assert result.exit_code == 0
        ctx.client.post.assert_called_once()

    def test_install_image_missing_flavour(self, cli_runner):
        """Test install image requires --flavour option"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install", "srv-12345", "--password", "pass", "--yes"],
            ctx
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_install_image_password_prompt(self, cli_runner):
        """Test install image prompts for password if not provided"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {"task_id": "task-001"}

        # Simulate password prompt with confirmation
        result = invoke_with_mocks(
            cli_runner,
            ["images", "install", "srv-12345", "--flavour", "ubuntu-22.04", "--yes"],
            ctx,
            input="SecurePass123\nSecurePass123\n"
        )

        assert result.exit_code == 0
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["password"] == "SecurePass123"

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_install_image_api_errors(self, cli_runner, status_code):
        """Test install image handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install", "srv-12345", "--flavour", "ubuntu-22.04", "--password", "pass", "--yes"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # install_custom_image tests
    def test_install_custom_image_with_confirm(self, cli_runner):
        """Test install custom image with --confirm flag"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {"task_id": "task-001"}

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install-custom", "srv-12345", "--image", "my-custom-image", "--confirm"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Custom image installation started" in result.output
        ctx.client.post.assert_called_once()
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/user-image"
        assert call_args[1]["json"]["key"] == "my-custom-image"

    def test_install_custom_image_with_yes_flag(self, cli_runner):
        """Test install custom image with --yes flag"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {"task_id": "task-001"}

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install-custom", "srv-12345", "--image", "my-image", "--yes"],
            ctx
        )

        assert result.exit_code == 0
        ctx.client.post.assert_called_once()

    def test_install_custom_image_with_confirmation(self, cli_runner):
        """Test install custom image with user confirmation"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {"task_id": "task-001"}

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install-custom", "srv-12345", "--image", "my-image"],
            ctx,
            input="y\n"
        )

        assert result.exit_code == 0
        ctx.client.post.assert_called_once()

    def test_install_custom_image_abort(self, cli_runner):
        """Test install custom image abort on confirmation"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install-custom", "srv-12345", "--image", "my-image"],
            ctx,
            input="n\n"
        )

        assert result.exit_code == 1
        assert "Aborted" in result.output
        ctx.client.post.assert_not_called()

    def test_install_custom_image_missing_image(self, cli_runner):
        """Test install custom image requires --image option"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install-custom", "srv-12345", "--yes"],
            ctx
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @pytest.mark.parametrize("status_code", [401, 404, 422, 500])
    def test_install_custom_image_api_errors(self, cli_runner, status_code):
        """Test install custom image handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["images", "install-custom", "srv-12345", "--image", "my-image", "--yes"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output
