"""
Tests for netcupctl.commands.custom_isos
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    CUSTOM_ISO_LIST_RESPONSE,
    CUSTOM_ISO_DETAIL_RESPONSE,
    UPLOAD_INIT_RESPONSE,
    UPLOAD_PART_RESPONSE,
    UPLOAD_COMPLETE_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestCustomISOsCommands:
    """Test suite for custom ISO management commands"""

    # list_isos tests
    def test_list_isos_success(self, cli_runner):
        """Test list custom ISOs successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = CUSTOM_ISO_LIST_RESPONSE

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["custom-isos", "list"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123/isos")

    def test_list_isos_empty_list(self, cli_runner):
        """Test list custom ISOs with empty result"""
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["custom-isos", "list"], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_list_isos_api_errors(self, cli_runner, status_code):
        """Test list ISOs handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["custom-isos", "list"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # get_iso tests
    def test_get_iso_success(self, cli_runner):
        """Test get custom ISO successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = CUSTOM_ISO_DETAIL_RESPONSE

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "get", "my-rescue-iso"],
                ctx
            )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123/isos/my-rescue-iso")

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_get_iso_api_errors(self, cli_runner, status_code):
        """Test get ISO handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "get", "my-iso"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # delete_iso tests
    def test_delete_iso_with_confirmation(self, cli_runner):
        """Test delete custom ISO with confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "delete", "my-iso"],
                ctx,
                input="y\n"
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Custom ISO deleted" in result.output
        ctx.client.delete.assert_called_once_with("/api/v1/users/user_123/isos/my-iso")

    def test_delete_iso_abort(self, cli_runner):
        """Test delete ISO abort on confirmation"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "delete", "my-iso"],
                ctx,
                input="n\n"
            )

        assert result.exit_code == 1
        assert "Aborted" in result.output
        ctx.client.delete.assert_not_called()

    def test_delete_iso_with_yes_flag(self, cli_runner):
        """Test delete ISO with --yes flag skips confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "delete", "my-iso", "--yes"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    def test_delete_iso_with_confirm_flag(self, cli_runner):
        """Test delete ISO with --confirm flag skips prompt"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "delete", "my-iso", "--confirm"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_delete_iso_api_errors(self, cli_runner, status_code):
        """Test delete ISO handles API errors"""
        ctx = create_mock_context()
        ctx.client.delete.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "delete", "my-iso", "--yes"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # upload_iso tests
    def test_upload_iso_success_default_name(self, cli_runner, tmp_path):
        """Test upload ISO successfully with default name"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = [UPLOAD_INIT_RESPONSE, UPLOAD_COMPLETE_RESPONSE]
        ctx.client.put_binary.return_value = UPLOAD_PART_RESPONSE

        # Create test file
        test_file = tmp_path / "test-rescue.iso"
        test_file.write_bytes(b"test" * 1000)  # 4KB file

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            with patch("netcupctl.commands.custom_isos.click.progressbar") as mock_progressbar:
                mock_progress = MagicMock()
                mock_progressbar.return_value.__enter__.return_value = mock_progress

                result = invoke_with_mocks(
                    cli_runner,
                    ["custom-isos", "upload", str(test_file)],
                    ctx
                )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "uploaded successfully" in result.output

        # Verify init call
        assert ctx.client.post.call_count == 2
        init_call = ctx.client.post.call_args_list[0]
        assert init_call[0][0] == "/api/v1/users/user_123/isos/test-rescue.iso"

        # Verify part upload
        ctx.client.put_binary.assert_called_once()

        # Verify complete call
        complete_call = ctx.client.post.call_args_list[1]
        assert complete_call[0][0] == "/api/v1/users/user_123/isos/test-rescue.iso/upload-abc123def456"

    def test_upload_iso_success_custom_name(self, cli_runner, tmp_path):
        """Test upload ISO successfully with custom --name"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = [UPLOAD_INIT_RESPONSE, UPLOAD_COMPLETE_RESPONSE]
        ctx.client.put_binary.return_value = UPLOAD_PART_RESPONSE

        test_file = tmp_path / "original.iso"
        test_file.write_bytes(b"test" * 1000)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            with patch("netcupctl.commands.custom_isos.click.progressbar") as mock_progressbar:
                mock_progress = MagicMock()
                mock_progressbar.return_value.__enter__.return_value = mock_progress

                result = invoke_with_mocks(
                    cli_runner,
                    ["custom-isos", "upload", str(test_file), "--name", "custom-rescue"],
                    ctx
                )

        assert result.exit_code == 0
        # Verify custom name used
        init_call = ctx.client.post.call_args_list[0]
        assert init_call[0][0] == "/api/v1/users/user_123/isos/custom-rescue"

    def test_upload_iso_init_failed_no_upload_id(self, cli_runner, tmp_path):
        """Test upload ISO when init returns no uploadId"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}  # No uploadId

        test_file = tmp_path / "test.iso"
        test_file.write_bytes(b"test")

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "upload", str(test_file)],
                ctx
            )

        assert result.exit_code == 1
        assert "Failed to initiate upload" in result.output
        ctx.client.put_binary.assert_not_called()

    def test_upload_iso_part_upload_failed_cleanup(self, cli_runner, tmp_path):
        """Test upload ISO handles part upload failure with cleanup"""
        ctx = create_mock_context()
        ctx.client.post.return_value = UPLOAD_INIT_RESPONSE
        ctx.client.put_binary.side_effect = APIError("Upload failed", status_code=500)
        ctx.client.delete.return_value = {}

        test_file = tmp_path / "test.iso"
        test_file.write_bytes(b"test" * 1000)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            with patch("netcupctl.commands.custom_isos.click.progressbar") as mock_progressbar:
                mock_progress = MagicMock()
                mock_progressbar.return_value.__enter__.return_value = mock_progress

                result = invoke_with_mocks(
                    cli_runner,
                    ["custom-isos", "upload", str(test_file)],
                    ctx
                )

        assert result.exit_code == 1
        assert "Upload failed" in result.output
        assert "Aborting upload" in result.output

        # Verify cleanup was attempted
        ctx.client.delete.assert_called_once_with(
            "/api/v1/users/user_123/isos/test.iso/upload-abc123def456"
        )

    def test_upload_iso_complete_failed_cleanup(self, cli_runner, tmp_path):
        """Test upload ISO handles complete failure with cleanup"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = [
            UPLOAD_INIT_RESPONSE,
            APIError("Complete failed", status_code=500)
        ]
        ctx.client.put_binary.return_value = UPLOAD_PART_RESPONSE
        ctx.client.delete.return_value = {}

        test_file = tmp_path / "test.iso"
        test_file.write_bytes(b"test" * 1000)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            with patch("netcupctl.commands.custom_isos.click.progressbar") as mock_progressbar:
                mock_progress = MagicMock()
                mock_progressbar.return_value.__enter__.return_value = mock_progress

                result = invoke_with_mocks(
                    cli_runner,
                    ["custom-isos", "upload", str(test_file)],
                    ctx
                )

        assert result.exit_code == 1
        assert "Upload failed" in result.output
        # Verify cleanup attempted
        ctx.client.delete.assert_called_once()

    def test_upload_iso_file_not_found(self, cli_runner):
        """Test upload ISO with non-existent file"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "upload", "/nonexistent/file.iso"],
                ctx
            )

        assert result.exit_code != 0
        # Click handles file existence check
        ctx.client.post.assert_not_called()

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_upload_iso_init_api_errors(self, cli_runner, tmp_path, status_code):
        """Test upload ISO handles API errors during init"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        test_file = tmp_path / "test.iso"
        test_file.write_bytes(b"test")

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["custom-isos", "upload", str(test_file)],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    def test_upload_iso_progress_bar_updates(self, cli_runner, tmp_path):
        """Test upload ISO updates progress bar correctly"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = [UPLOAD_INIT_RESPONSE, UPLOAD_COMPLETE_RESPONSE]
        ctx.client.put_binary.return_value = UPLOAD_PART_RESPONSE

        test_file = tmp_path / "test.iso"
        test_data = b"x" * 4000
        test_file.write_bytes(test_data)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            with patch("netcupctl.commands.custom_isos.click.progressbar") as mock_progressbar:
                mock_progress = MagicMock()
                mock_progressbar.return_value.__enter__.return_value = mock_progress

                result = invoke_with_mocks(
                    cli_runner,
                    ["custom-isos", "upload", str(test_file)],
                    ctx
                )

        assert result.exit_code == 0
        # Verify progress.update was called with chunk size
        mock_progress.update.assert_called()
        assert mock_progress.update.call_count >= 1

    def test_upload_iso_cleanup_failure_silenced(self, cli_runner, tmp_path):
        """Test upload cleanup failure is silently handled"""
        ctx = create_mock_context()
        ctx.client.post.return_value = UPLOAD_INIT_RESPONSE
        ctx.client.put_binary.side_effect = APIError("Upload failed", status_code=500)
        ctx.client.delete.side_effect = APIError("Delete failed", status_code=404)

        test_file = tmp_path / "test.iso"
        test_file.write_bytes(b"test" * 1000)

        with patch("netcupctl.commands.custom_isos.get_authenticated_user_id", return_value="user_123"):
            with patch("netcupctl.commands.custom_isos.click.progressbar") as mock_progressbar:
                mock_progress = MagicMock()
                mock_progressbar.return_value.__enter__.return_value = mock_progress

                result = invoke_with_mocks(
                    cli_runner,
                    ["custom-isos", "upload", str(test_file)],
                    ctx
                )

        assert result.exit_code == 1
        # Cleanup failure should be silenced (pass)
        ctx.client.delete.assert_called_once()
