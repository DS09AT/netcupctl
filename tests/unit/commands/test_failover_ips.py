"""
Tests for netcupctl.commands.failover_ips
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    FAILOVER_IP_LIST_RESPONSE,
    FAILOVER_IP_DETAIL_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestFailoverIPsCommands:
    """Test suite for failover IP management commands"""

    # list_failover_ips tests
    def test_list_failover_ips_both_versions(self, cli_runner):
        """Test list failover IPs for both v4 and v6"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [
            [{"id": "fip-001", "ip": "203.0.113.100"}],  # v4
            [{"id": "fip-002", "ip": "2001:db8::100"}],  # v6
        ]

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["failover-ips", "list"], ctx)

        assert result.exit_code == 0
        assert ctx.client.get.call_count == 2

    def test_list_failover_ips_v4_only(self, cli_runner):
        """Test list failover IPs filtered to v4"""
        ctx = create_mock_context()
        ctx.client.get.return_value = [{"id": "fip-001", "ip": "203.0.113.100"}]

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "list", "--version", "v4"],
                ctx
            )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123/failoverips/v4")

    def test_list_failover_ips_v6_only(self, cli_runner):
        """Test list failover IPs filtered to v6"""
        ctx = create_mock_context()
        ctx.client.get.return_value = [{"id": "fip-002", "ip": "2001:db8::100"}]

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "list", "--version", "v6"],
                ctx
            )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123/failoverips/v6")

    def test_list_failover_ips_v4_not_found_v6_ok(self, cli_runner):
        """Test list when v4 API errors but v6 succeeds"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [
            APIError("Not found", status_code=404),  # v4
            [{"id": "fip-002", "ip": "2001:db8::100"}],  # v6
        ]

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["failover-ips", "list"], ctx)

        assert result.exit_code == 0  # Should succeed with v6 results
        assert ctx.client.get.call_count == 2

    def test_list_failover_ips_empty_list(self, cli_runner):
        """Test list failover IPs with empty results"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [
            APIError("Not found", status_code=404),  # v4
            APIError("Not found", status_code=404),  # v6
        ]

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["failover-ips", "list"], ctx)

        assert result.exit_code == 0  # Should succeed with empty list

    def test_list_failover_ips_single_dict_response(self, cli_runner):
        """Test list when API returns single dict instead of list"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [
            {"id": "fip-001", "ip": "203.0.113.100"},  # Single dict v4
            APIError("Not found", status_code=404),  # v6
        ]

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["failover-ips", "list"], ctx)

        assert result.exit_code == 0

    def test_list_failover_ips_auth_error_on_user_id(self, cli_runner):
        """Test list failover IPs handles auth errors during user ID lookup"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id") as mock_user_id:
            mock_user_id.side_effect = APIError("Unauthorized", status_code=401)
            result = invoke_with_mocks(cli_runner, ["failover-ips", "list"], ctx)

        assert result.exit_code == 401
        assert "Error:" in result.output

    # get_failover_ip tests
    def test_get_failover_ip_v4_success(self, cli_runner):
        """Test get failover IP v4 successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FAILOVER_IP_DETAIL_RESPONSE

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "get", "fip-001", "--version", "v4"],
                ctx
            )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123/failoverips/v4/fip-001")

    def test_get_failover_ip_v6_success(self, cli_runner):
        """Test get failover IP v6 successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FAILOVER_IP_DETAIL_RESPONSE

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "get", "fip-002", "--version", "v6"],
                ctx
            )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with("/api/v1/users/user_123/failoverips/v6/fip-002")

    def test_get_failover_ip_missing_version(self, cli_runner):
        """Test get failover IP requires --version option"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "get", "fip-001"],
                ctx
            )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_get_failover_ip_api_errors(self, cli_runner, status_code):
        """Test get failover IP handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "get", "fip-001", "--version", "v4"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # update_failover_ip tests
    def test_update_failover_ip_with_server(self, cli_runner):
        """Test update failover IP with --server option"""
        ctx = create_mock_context()
        ctx.client.patch.return_value = FAILOVER_IP_DETAIL_RESPONSE

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "update", "fip-001", "--version", "v4", "--server", "srv-12345"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Failover IP updated" in result.output
        ctx.client.patch.assert_called_once()
        call_args = ctx.client.patch.call_args
        assert call_args[0][0] == "/api/v1/users/user_123/failoverips/v4/fip-001"
        assert call_args[1]["json"]["serverId"] == "srv-12345"

    def test_update_failover_ip_with_mac(self, cli_runner):
        """Test update failover IP with --mac option"""
        ctx = create_mock_context()
        ctx.client.patch.return_value = FAILOVER_IP_DETAIL_RESPONSE

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "update", "fip-001", "--version", "v4", "--mac", "00:11:22:33:44:55"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.patch.call_args
        assert call_args[1]["json"]["mac"] == "00:11:22:33:44:55"

    def test_update_failover_ip_with_both_options(self, cli_runner):
        """Test update failover IP with both --server and --mac"""
        ctx = create_mock_context()
        ctx.client.patch.return_value = FAILOVER_IP_DETAIL_RESPONSE

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "update", "fip-001", "--version", "v6", "--server", "srv-67890", "--mac", "00:11:22:33:44:66"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.patch.call_args
        assert call_args[1]["json"]["serverId"] == "srv-67890"
        assert call_args[1]["json"]["mac"] == "00:11:22:33:44:66"

    def test_update_failover_ip_no_updates(self, cli_runner):
        """Test update failover IP without any update options fails"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "update", "fip-001", "--version", "v4"],
                ctx
            )

        assert result.exit_code != 0
        assert "at least one update option" in result.output
        ctx.client.patch.assert_not_called()

    def test_update_failover_ip_missing_version(self, cli_runner):
        """Test update failover IP requires --version option"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "update", "fip-001", "--server", "srv-12345"],
                ctx
            )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @pytest.mark.parametrize("status_code", [401, 404, 422, 500])
    def test_update_failover_ip_api_errors(self, cli_runner, status_code):
        """Test update failover IP handles API errors"""
        ctx = create_mock_context()
        ctx.client.patch.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.failover_ips.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["failover-ips", "update", "fip-001", "--version", "v4", "--server", "srv-12345"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output
