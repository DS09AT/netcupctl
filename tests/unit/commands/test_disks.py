import pytest
from unittest.mock import MagicMock
from click.testing import CliRunner

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import DISK_LIST_RESPONSE
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestDisksCommands:

    def test_list_disks_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = DISK_LIST_RESPONSE

        result = invoke_with_mocks(cli_runner, ["disks", "list", "srv-12345"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once()

    def test_list_disks_invalid_server_id(self, cli_runner):
        ctx = create_mock_context()

        result = invoke_with_mocks(cli_runner, ["disks", "list", "../../../etc"], ctx)

        assert result.exit_code != 0

    def test_get_disk_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = DISK_LIST_RESPONSE[0]

        result = invoke_with_mocks(cli_runner, ["disks", "get", "srv-12345", "system-disk"], ctx)

        assert result.exit_code == 0

    def test_get_disk_invalid_name(self, cli_runner):
        ctx = create_mock_context()

        result = invoke_with_mocks(cli_runner, ["disks", "get", "srv-12345", "disk;rm -rf /"], ctx)

        assert result.exit_code != 0

    def test_list_drivers_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.get.return_value = ["virtio", "ide", "scsi"]

        result = invoke_with_mocks(cli_runner, ["disks", "drivers", "srv-12345"], ctx)

        assert result.exit_code == 0

    def test_set_driver_success(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.patch.return_value = {"driver": "virtio"}

        result = invoke_with_mocks(
            cli_runner, ["disks", "set-driver", "srv-12345", "--driver", "virtio"], ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output

    def test_set_driver_missing_option(self, cli_runner):
        ctx = create_mock_context()

        result = invoke_with_mocks(cli_runner, ["disks", "set-driver", "srv-12345"], ctx)

        assert result.exit_code != 0

    def test_format_disk_with_yes_flag(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.post.return_value = {"status": "formatting"}

        result = invoke_with_mocks(
            cli_runner, ["disks", "format", "srv-12345", "data-disk", "--yes"], ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output

    def test_format_disk_with_confirm_flag(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.post.return_value = {"status": "formatting"}

        result = invoke_with_mocks(
            cli_runner, ["disks", "format", "srv-12345", "data-disk", "--confirm"], ctx
        )

        assert result.exit_code == 0

    def test_format_disk_abort_without_confirmation(self, cli_runner):
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner, ["disks", "format", "srv-12345", "data-disk"], ctx, input="n\n"
        )

        assert result.exit_code != 0
        ctx.client.post.assert_not_called()

    def test_format_disk_api_error(self, cli_runner):
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Cannot format", status_code=400)

        result = invoke_with_mocks(
            cli_runner, ["disks", "format", "srv-12345", "data-disk", "--yes"], ctx
        )

        assert result.exit_code == 400

    @pytest.mark.parametrize("disk_name", [
        "valid-disk",
        "disk_123",
        "disk.bak",
    ])
    def test_valid_disk_names(self, cli_runner, disk_name):
        ctx = create_mock_context()
        ctx.client.get.return_value = {"name": disk_name}

        result = invoke_with_mocks(cli_runner, ["disks", "get", "srv-123", disk_name], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("disk_name", [
        "disk/path",
        "disk;cmd",
        "a" * 100,
    ])
    def test_invalid_disk_names(self, cli_runner, disk_name):
        ctx = create_mock_context()

        result = invoke_with_mocks(cli_runner, ["disks", "get", "srv-123", disk_name], ctx)

        assert result.exit_code != 0
