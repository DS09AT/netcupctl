"""
Tests for netcupctl.commands.snapshots
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    SNAPSHOT_LIST_RESPONSE,
    SNAPSHOT_DETAIL_RESPONSE,
    SNAPSHOT_CREATE_RESPONSE,
    SNAPSHOT_EXPORT_RESPONSE,
    SNAPSHOT_DRYRUN_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestSnapshotsCommands:
    """Test suite for snapshot management commands"""

    # list_snapshots tests
    def test_list_snapshots_success(self, cli_runner):
        """Test list snapshots successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = SNAPSHOT_LIST_RESPONSE

        result = invoke_with_mocks(cli_runner, ["snapshots", "list", "srv-12345"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/servers/srv-12345/snapshots")

    def test_list_snapshots_empty_list(self, cli_runner):
        """Test list snapshots with empty result"""
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        result = invoke_with_mocks(cli_runner, ["snapshots", "list", "srv-12345"], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_list_snapshots_api_errors(self, cli_runner, status_code):
        """Test list snapshots handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(cli_runner, ["snapshots", "list", "srv-12345"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # get_snapshot tests
    def test_get_snapshot_success(self, cli_runner):
        """Test get snapshot successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = SNAPSHOT_DETAIL_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "get", "srv-12345", "backup-2024-01-15"],
            ctx
        )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/servers/srv-12345/snapshots/backup-2024-01-15")

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_get_snapshot_api_errors(self, cli_runner, status_code):
        """Test get snapshot handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "get", "srv-12345", "test-snapshot"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # create_snapshot tests
    def test_create_snapshot_success(self, cli_runner):
        """Test create snapshot successfully"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SNAPSHOT_CREATE_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "create", "srv-12345", "--name", "my-backup"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Snapshot creation initiated" in result.output
        ctx.client.post.assert_called_once()
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/snapshots"
        assert call_args[1]["json"]["name"] == "my-backup"
        assert call_args[1]["json"]["description"] == ""

    def test_create_snapshot_with_description(self, cli_runner):
        """Test create snapshot with description"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SNAPSHOT_CREATE_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "create", "srv-12345", "--name", "my-backup", "--description", "Daily backup"],
            ctx
        )

        assert result.exit_code == 0
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["description"] == "Daily backup"

    def test_create_snapshot_with_dry_run(self, cli_runner):
        """Test create snapshot with --dry-run flag"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SNAPSHOT_DRYRUN_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "create", "srv-12345", "--name", "test", "--dry-run"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Dry run completed" in result.output
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/snapshots:dryrun"

    def test_create_snapshot_missing_name(self, cli_runner):
        """Test create snapshot requires --name option"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "create", "srv-12345"],
            ctx
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_create_snapshot_api_errors(self, cli_runner, status_code):
        """Test create snapshot handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "create", "srv-12345", "--name", "test"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # delete_snapshot tests
    def test_delete_snapshot_with_confirmation(self, cli_runner):
        """Test delete snapshot with confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "delete", "srv-12345", "old-backup"],
            ctx,
            input="y\n"
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Snapshot deleted" in result.output
        ctx.client.delete.assert_called_once_with("/api/v1/servers/srv-12345/snapshots/old-backup")

    def test_delete_snapshot_abort(self, cli_runner):
        """Test delete snapshot abort on confirmation"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "delete", "srv-12345", "important-backup"],
            ctx,
            input="n\n"
        )

        assert result.exit_code == 1
        assert "Aborted" in result.output
        ctx.client.delete.assert_not_called()

    def test_delete_snapshot_with_yes_flag(self, cli_runner):
        """Test delete snapshot with --yes flag skips confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "delete", "srv-12345", "old-backup", "--yes"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    def test_delete_snapshot_with_confirm_flag(self, cli_runner):
        """Test delete snapshot with --confirm flag skips prompt"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "delete", "srv-12345", "old-backup", "--confirm"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_delete_snapshot_api_errors(self, cli_runner, status_code):
        """Test delete snapshot handles API errors"""
        ctx = create_mock_context()
        ctx.client.delete.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "delete", "srv-12345", "test", "--yes"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # revert_snapshot tests
    def test_revert_snapshot_with_confirmation(self, cli_runner):
        """Test revert snapshot with confirmation (destructive)"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "revert", "srv-12345", "backup-2024-01-15"],
            ctx,
            input="y\n"
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Snapshot revert initiated" in result.output
        ctx.client.post.assert_called_once_with("/api/v1/servers/srv-12345/snapshots/backup-2024-01-15/revert")

    def test_revert_snapshot_abort(self, cli_runner):
        """Test revert snapshot abort on confirmation"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "revert", "srv-12345", "backup"],
            ctx,
            input="n\n"
        )

        assert result.exit_code == 1
        assert "Aborted" in result.output
        ctx.client.post.assert_not_called()

    def test_revert_snapshot_with_yes_flag(self, cli_runner):
        """Test revert snapshot with --yes flag skips confirmation"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "revert", "srv-12345", "backup", "--yes"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.post.assert_called_once()

    def test_revert_snapshot_with_confirm_flag(self, cli_runner):
        """Test revert snapshot with --confirm flag skips prompt"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "revert", "srv-12345", "backup", "--confirm"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.post.assert_called_once()

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_revert_snapshot_api_errors(self, cli_runner, status_code):
        """Test revert snapshot handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "revert", "srv-12345", "backup", "--yes"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # export_snapshot tests
    def test_export_snapshot_success(self, cli_runner):
        """Test export snapshot successfully"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SNAPSHOT_EXPORT_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "export", "srv-12345", "backup-2024-01-15"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Snapshot export initiated" in result.output
        ctx.client.post.assert_called_once_with("/api/v1/servers/srv-12345/snapshots/backup-2024-01-15/export")

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_export_snapshot_api_errors(self, cli_runner, status_code):
        """Test export snapshot handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "export", "srv-12345", "backup"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # dryrun_snapshot tests
    def test_dryrun_snapshot_success(self, cli_runner):
        """Test dryrun snapshot successfully"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SNAPSHOT_DRYRUN_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "dryrun", "srv-12345", "--name", "test-snapshot"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Dry run completed" in result.output
        ctx.client.post.assert_called_once()
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/snapshots:dryrun"
        assert call_args[1]["json"]["name"] == "test-snapshot"

    def test_dryrun_snapshot_with_description(self, cli_runner):
        """Test dryrun snapshot with description"""
        ctx = create_mock_context()
        ctx.client.post.return_value = SNAPSHOT_DRYRUN_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "dryrun", "srv-12345", "--name", "test", "--description", "Test description"],
            ctx
        )

        assert result.exit_code == 0
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["description"] == "Test description"

    def test_dryrun_snapshot_missing_name(self, cli_runner):
        """Test dryrun snapshot requires --name option"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "dryrun", "srv-12345"],
            ctx
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_dryrun_snapshot_api_errors(self, cli_runner, status_code):
        """Test dryrun snapshot handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["snapshots", "dryrun", "srv-12345", "--name", "test"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output
