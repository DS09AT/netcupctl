"""
Tests for netcupctl.commands.iso
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    ISO_LIST_RESPONSE,
    ISO_DETAIL_RESPONSE,
    ISO_MOUNT_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestISOCommands:
    """Test suite for ISO management commands"""

    # list_images tests
    def test_list_images_success(self, cli_runner):
        """Test list ISO images successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = ISO_LIST_RESPONSE

        result = invoke_with_mocks(cli_runner, ["iso", "images", "srv-12345"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/servers/srv-12345/isoimages")

    def test_list_images_empty_list(self, cli_runner):
        """Test list ISO images with empty result"""
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        result = invoke_with_mocks(cli_runner, ["iso", "images", "srv-12345"], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_list_images_api_errors(self, cli_runner, status_code):
        """Test list ISO images handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(cli_runner, ["iso", "images", "srv-12345"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # show_iso tests
    def test_show_iso_mounted(self, cli_runner):
        """Test show ISO when one is mounted"""
        ctx = create_mock_context()
        ctx.client.get.return_value = ISO_DETAIL_RESPONSE

        result = invoke_with_mocks(cli_runner, ["iso", "show", "srv-12345"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/servers/srv-12345/iso")

    def test_show_iso_no_iso_mounted_null(self, cli_runner):
        """Test show ISO when none mounted (null response)"""
        ctx = create_mock_context()
        ctx.client.get.return_value = None

        result = invoke_with_mocks(cli_runner, ["iso", "show", "srv-12345"], ctx)

        assert result.exit_code == 0
        assert "No ISO mounted" in result.output

    def test_show_iso_no_iso_mounted_404(self, cli_runner):
        """Test show ISO when none mounted (404 error)"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Not found", status_code=404)

        result = invoke_with_mocks(cli_runner, ["iso", "show", "srv-12345"], ctx)

        assert result.exit_code == 0
        assert "No ISO mounted" in result.output

    @pytest.mark.parametrize("status_code", [401, 500])
    def test_show_iso_api_errors(self, cli_runner, status_code):
        """Test show ISO handles non-404 API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(cli_runner, ["iso", "show", "srv-12345"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # mount_iso tests
    def test_mount_iso_success(self, cli_runner):
        """Test mount ISO successfully"""
        ctx = create_mock_context()
        ctx.client.post.return_value = ISO_MOUNT_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["iso", "mount", "srv-12345", "ubuntu-22.04-server.iso"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "ISO mounted" in result.output
        ctx.client.post.assert_called_once()
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/iso"
        assert call_args[1]["json"]["isoImage"] == "ubuntu-22.04-server.iso"

    @pytest.mark.parametrize("status_code", [401, 404, 422, 500])
    def test_mount_iso_api_errors(self, cli_runner, status_code):
        """Test mount ISO handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["iso", "mount", "srv-12345", "test.iso"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # unmount_iso tests
    def test_unmount_iso_success(self, cli_runner):
        """Test unmount ISO successfully"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        result = invoke_with_mocks(cli_runner, ["iso", "unmount", "srv-12345"], ctx)

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "ISO unmounted" in result.output
        ctx.client.delete.assert_called_once_with("/api/v1/servers/srv-12345/iso")

    def test_unmount_iso_no_iso_mounted(self, cli_runner):
        """Test unmount ISO when none is mounted (404)"""
        ctx = create_mock_context()
        ctx.client.delete.side_effect = APIError("Not found", status_code=404)

        result = invoke_with_mocks(cli_runner, ["iso", "unmount", "srv-12345"], ctx)

        assert result.exit_code == 0
        assert "No ISO was mounted" in result.output

    @pytest.mark.parametrize("status_code", [401, 500])
    def test_unmount_iso_api_errors(self, cli_runner, status_code):
        """Test unmount ISO handles non-404 API errors"""
        ctx = create_mock_context()
        ctx.client.delete.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(cli_runner, ["iso", "unmount", "srv-12345"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output
