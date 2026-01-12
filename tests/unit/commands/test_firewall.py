"""
Tests for netcupctl.commands.firewall
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    FIREWALL_RULES_RESPONSE,
    FIREWALL_STATUS_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestFirewallCommands:
    """Test suite for firewall management commands"""

    # show_firewall tests
    def test_show_firewall_success(self, cli_runner):
        """Test show firewall rules successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_RULES_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "show", "srv-12345", "00:11:22:33:44:55"],
            ctx
        )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with(
            "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall",
            params=None
        )

    def test_show_firewall_with_check_flag(self, cli_runner):
        """Test show firewall with --check flag"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_RULES_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "show", "srv-12345", "00:11:22:33:44:55", "--check"],
            ctx
        )

        assert result.exit_code == 0
        call_args = ctx.client.get.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall"
        assert call_args[1]["params"]["consistencyCheck"] == "true"

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_show_firewall_api_errors(self, cli_runner, status_code):
        """Test show firewall handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "show", "srv-12345", "00:11:22:33:44:55"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # set_firewall tests
    def test_set_firewall_with_rules_string(self, cli_runner):
        """Test set firewall with --rules JSON string"""
        ctx = create_mock_context()
        ctx.client.put.return_value = FIREWALL_RULES_RESPONSE

        rules_json = '{"rules": [{"protocol": "tcp", "port": "22", "action": "allow"}]}'

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55", "--rules", rules_json],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Firewall rules updated" in result.output
        ctx.client.put.assert_called_once()
        call_args = ctx.client.put.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall"
        assert "rules" in call_args[1]["json"]

    def test_set_firewall_with_rules_file(self, cli_runner, tmp_path):
        """Test set firewall with --rules-file"""
        ctx = create_mock_context()
        ctx.client.put.return_value = FIREWALL_RULES_RESPONSE

        rules_file = tmp_path / "firewall-rules.json"
        rules_file.write_text('{"rules": [{"protocol": "tcp", "port": "80", "action": "allow"}], "default_policy": "drop"}')

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55", "--rules-file", str(rules_file)],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["rules"][0]["port"] == "80"
        assert call_args[1]["json"]["default_policy"] == "drop"

    def test_set_firewall_missing_both_options(self, cli_runner):
        """Test set firewall without --rules or --rules-file fails"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55"],
            ctx
        )

        assert result.exit_code != 0
        assert "Provide --rules or --rules-file" in result.output
        ctx.client.put.assert_not_called()

    def test_set_firewall_invalid_json(self, cli_runner):
        """Test set firewall with invalid JSON"""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55", "--rules", "invalid json"],
            ctx
        )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output
        ctx.client.put.assert_not_called()

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_set_firewall_api_errors(self, cli_runner, status_code):
        """Test set firewall handles API errors"""
        ctx = create_mock_context()
        ctx.client.put.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55", "--rules", '{"rules": []}'],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # reapply_firewall tests
    def test_reapply_firewall_success(self, cli_runner):
        """Test reapply firewall successfully"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "reapply", "srv-12345", "00:11:22:33:44:55"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Firewall rules reapplied" in result.output
        ctx.client.post.assert_called_once_with(
            "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall:reapply"
        )

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_reapply_firewall_api_errors(self, cli_runner, status_code):
        """Test reapply firewall handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "reapply", "srv-12345", "00:11:22:33:44:55"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # restore_firewall tests
    def test_restore_firewall_success(self, cli_runner):
        """Test restore firewall policies successfully"""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "restore", "srv-12345", "00:11:22:33:44:55"],
            ctx
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Firewall policies restored" in result.output
        ctx.client.post.assert_called_once_with(
            "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall:restore-copied-policies"
        )

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_restore_firewall_api_errors(self, cli_runner, status_code):
        """Test restore firewall handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "restore", "srv-12345", "00:11:22:33:44:55"],
            ctx
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output
