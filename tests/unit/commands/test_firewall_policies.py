"""
Tests for netcupctl.commands.firewall_policies
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    FIREWALL_POLICY_LIST_RESPONSE,
    FIREWALL_POLICY_DETAIL_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestFirewallPoliciesCommands:
    """Test suite for firewall policy management commands"""

    # list_policies tests
    def test_list_policies_success(self, cli_runner):
        """Test list firewall policies successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_RESPONSE

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["firewall-policies", "list"], ctx)

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with(
            "/api/v1/users/user_123/firewall-policies",
            params={"limit": 50, "offset": 0}
        )

    def test_list_policies_with_search(self, cli_runner):
        """Test list policies with search query"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_RESPONSE

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "list", "--search", "web-server"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.get.call_args
        assert call_args[0][0] == "/api/v1/users/user_123/firewall-policies"
        assert call_args[1]["params"]["q"] == "web-server"

    def test_list_policies_with_limit_offset(self, cli_runner):
        """Test list policies with custom limit and offset"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_RESPONSE

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "list", "--limit", "100", "--offset", "50"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.get.call_args
        assert call_args[1]["params"]["limit"] == 100
        assert call_args[1]["params"]["offset"] == 50

    def test_list_policies_empty_list(self, cli_runner):
        """Test list policies with empty result"""
        ctx = create_mock_context()
        ctx.client.get.return_value = []

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["firewall-policies", "list"], ctx)

        assert result.exit_code == 0

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_list_policies_api_errors(self, cli_runner, status_code):
        """Test list policies handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(cli_runner, ["firewall-policies", "list"], ctx)

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # get_policy tests
    def test_get_policy_success(self, cli_runner):
        """Test get firewall policy successfully"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "get", "policy-001"],
                ctx
            )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with(
            "/api/v1/users/user_123/firewall-policies/policy-001",
            params=None
        )

    def test_get_policy_with_count_flag(self, cli_runner):
        """Test get policy with --with-count flag"""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "get", "policy-001", "--with-count"],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.get.call_args
        assert call_args[0][0] == "/api/v1/users/user_123/firewall-policies/policy-001"
        assert call_args[1]["params"]["withCountOfAffectedServers"] == "true"

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_get_policy_api_errors(self, cli_runner, status_code):
        """Test get policy handles API errors"""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "get", "policy-001"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # create_policy tests
    def test_create_policy_with_rules_string(self, cli_runner):
        """Test create policy with --rules JSON string"""
        ctx = create_mock_context()
        ctx.client.post.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        rules_json = '{"description": "Allow HTTP", "rules": [{"protocol": "tcp", "port": "80"}]}'

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "create", "--name", "web-policy", "--rules", rules_json],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Firewall policy created" in result.output
        ctx.client.post.assert_called_once()
        call_args = ctx.client.post.call_args
        assert call_args[0][0] == "/api/v1/users/user_123/firewall-policies"
        assert call_args[1]["json"]["name"] == "web-policy"
        assert call_args[1]["json"]["description"] == "Allow HTTP"

    def test_create_policy_with_rules_file(self, cli_runner, tmp_path):
        """Test create policy with --rules-file"""
        ctx = create_mock_context()
        ctx.client.post.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        rules_file = tmp_path / "rules.json"
        rules_file.write_text('{"description": "SSH only", "rules": [{"protocol": "tcp", "port": "22"}]}')

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "create", "--name", "ssh-policy", "--rules-file", str(rules_file)],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["name"] == "ssh-policy"
        assert call_args[1]["json"]["description"] == "SSH only"

    def test_create_policy_without_rules(self, cli_runner):
        """Test create policy without rules (empty rules)"""
        ctx = create_mock_context()
        ctx.client.post.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "create", "--name", "empty-policy"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.post.call_args
        assert call_args[1]["json"]["name"] == "empty-policy"

    def test_create_policy_invalid_json(self, cli_runner):
        """Test create policy with invalid JSON"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "create", "--name", "test", "--rules", "invalid json"],
                ctx
            )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output
        ctx.client.post.assert_not_called()

    def test_create_policy_missing_name(self, cli_runner):
        """Test create policy requires --name option"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "create", "--rules", '{"test": true}'],
                ctx
            )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_create_policy_api_errors(self, cli_runner, status_code):
        """Test create policy handles API errors"""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "create", "--name", "test"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # update_policy tests
    def test_update_policy_name_only(self, cli_runner):
        """Test update policy name only"""
        ctx = create_mock_context()
        ctx.client.put.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "update", "policy-001", "--name", "new-name"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Firewall policy updated" in result.output
        ctx.client.put.assert_called_once()
        call_args = ctx.client.put.call_args
        assert call_args[0][0] == "/api/v1/users/user_123/firewall-policies/policy-001"
        assert call_args[1]["json"]["name"] == "new-name"

    def test_update_policy_with_rules_string(self, cli_runner):
        """Test update policy with --rules JSON string"""
        ctx = create_mock_context()
        ctx.client.put.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        rules_json = '{"rules": [{"protocol": "tcp", "port": "443"}]}'

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "update", "policy-001", "--rules", rules_json],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert "rules" in call_args[1]["json"]

    def test_update_policy_with_rules_file(self, cli_runner, tmp_path):
        """Test update policy with --rules-file"""
        ctx = create_mock_context()
        ctx.client.put.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        rules_file = tmp_path / "update-rules.json"
        rules_file.write_text('{"description": "Updated description"}')

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "update", "policy-001", "--rules-file", str(rules_file)],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["description"] == "Updated description"

    def test_update_policy_combined_options(self, cli_runner):
        """Test update policy with name and rules combined"""
        ctx = create_mock_context()
        ctx.client.put.return_value = FIREWALL_POLICY_DETAIL_RESPONSE

        rules_json = '{"description": "Combined update"}'

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "update", "policy-001", "--name", "updated-name", "--rules", rules_json],
                ctx
            )

        assert result.exit_code == 0
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["name"] == "updated-name"
        assert call_args[1]["json"]["description"] == "Combined update"

    def test_update_policy_no_updates(self, cli_runner):
        """Test update policy without any update options fails"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "update", "policy-001"],
                ctx
            )

        assert result.exit_code != 0
        assert "at least one update option" in result.output
        ctx.client.put.assert_not_called()

    def test_update_policy_invalid_json(self, cli_runner):
        """Test update policy with invalid JSON"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "update", "policy-001", "--rules", "invalid json"],
                ctx
            )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output
        ctx.client.put.assert_not_called()

    @pytest.mark.parametrize("status_code", [401, 404, 422, 500])
    def test_update_policy_api_errors(self, cli_runner, status_code):
        """Test update policy handles API errors"""
        ctx = create_mock_context()
        ctx.client.put.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "update", "policy-001", "--name", "test"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output

    # delete_policy tests
    def test_delete_policy_with_confirmation(self, cli_runner):
        """Test delete firewall policy with confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "delete", "policy-001"],
                ctx,
                input="y\n"
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Firewall policy deleted" in result.output
        ctx.client.delete.assert_called_once_with("/api/v1/users/user_123/firewall-policies/policy-001")

    def test_delete_policy_abort(self, cli_runner):
        """Test delete policy abort on confirmation"""
        ctx = create_mock_context()

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "delete", "policy-001"],
                ctx,
                input="n\n"
            )

        assert result.exit_code == 1
        assert "Aborted" in result.output
        ctx.client.delete.assert_not_called()

    def test_delete_policy_with_yes_flag(self, cli_runner):
        """Test delete policy with --yes flag skips confirmation"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "delete", "policy-001", "--yes"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    def test_delete_policy_with_confirm_flag(self, cli_runner):
        """Test delete policy with --confirm flag skips prompt"""
        ctx = create_mock_context()
        ctx.client.delete.return_value = {}

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "delete", "policy-001", "--confirm"],
                ctx
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.delete.assert_called_once()

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_delete_policy_api_errors(self, cli_runner, status_code):
        """Test delete policy handles API errors"""
        ctx = create_mock_context()
        ctx.client.delete.side_effect = APIError("Error", status_code=status_code)

        with patch("netcupctl.commands.firewall_policies.get_authenticated_user_id", return_value="user_123"):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall-policies", "delete", "policy-001", "--yes"],
                ctx
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output
