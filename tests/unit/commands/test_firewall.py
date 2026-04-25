"""Tests for netcupctl.commands.firewall."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from netcupctl.cli import cli
from netcupctl.client import APIError
from tests.fixtures.api_responses import (
    FIREWALL_GET_RESPONSE,
    FIREWALL_GET_WITH_COPIED,
    FIREWALL_GET_EMPTY,
    FIREWALL_POLICY_LIST_EMPTY_RESPONSE,
    FIREWALL_POLICY_LIST_ONE_RESPONSE,
    FIREWALL_POLICY_CREATE_RESPONSE,
)
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestFirewallCommands:
    """Tests for firewall management commands."""


    def test_show_firewall_success(self, cli_runner):
        """Show firewall rules successfully."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_GET_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "show", "srv-12345", "00:11:22:33:44:55"],
            ctx,
        )

        assert result.exit_code == 0
        ctx.client.get.assert_called_once_with(
            "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall",
            params=None,
        )

    def test_show_firewall_with_check_flag(self, cli_runner):
        """Show firewall with --check passes consistencyCheck param."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_GET_RESPONSE

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "show", "srv-12345", "00:11:22:33:44:55", "--check"],
            ctx,
        )

        assert result.exit_code == 0
        call_args = ctx.client.get.call_args
        assert call_args[1]["params"]["consistencyCheck"] == "true"

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_show_firewall_api_errors(self, cli_runner, status_code):
        """Show firewall exits with the HTTP status code on API errors."""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "show", "srv-12345", "00:11:22:33:44:55"],
            ctx,
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output


    def test_set_firewall_with_rules_string(self, cli_runner):
        """Set firewall with --rules JSON string succeeds."""
        ctx = create_mock_context()
        ctx.client.put.return_value = {}

        rules_json = '{"copiedPolicies":[],"userPolicies":[{"id":42}],"active":true}'

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55", "--rules", rules_json],
            ctx,
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.put.assert_called_once()
        call_args = ctx.client.put.call_args
        assert call_args[0][0] == "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall"
        assert call_args[1]["json"]["userPolicies"] == [{"id": 42}]

    def test_set_firewall_with_rules_file(self, cli_runner, tmp_path):
        """Set firewall with --rules-file loads JSON from the file."""
        ctx = create_mock_context()
        ctx.client.put.return_value = {}

        rules_file = tmp_path / "firewall.json"
        rules_file.write_text('{"copiedPolicies":[],"userPolicies":[{"id":10}],"active":true}')

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55", "--rules-file", str(rules_file)],
            ctx,
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        call_args = ctx.client.put.call_args
        assert call_args[1]["json"]["userPolicies"] == [{"id": 10}]

    def test_set_firewall_missing_both_options(self, cli_runner):
        """Set firewall without --rules or --rules-file fails with usage error."""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55"],
            ctx,
        )

        assert result.exit_code != 0
        assert "Provide --rules or --rules-file" in result.output
        ctx.client.put.assert_not_called()

    def test_set_firewall_invalid_json(self, cli_runner):
        """Set firewall with invalid JSON exits with code 1."""
        ctx = create_mock_context()

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55", "--rules", "invalid json"],
            ctx,
        )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output
        ctx.client.put.assert_not_called()

    def test_set_firewall_warns_when_both_policies_empty(self, cli_runner):
        """Set firewall warns when both userPolicies and copiedPolicies are empty (ACCEPT_ALL result)."""
        ctx = create_mock_context()
        ctx.client.put.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55",
             "--rules", '{"copiedPolicies":[],"userPolicies":[],"active":true}'],
            ctx,
        )

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "ACCEPT_ALL" in result.output

    def test_set_firewall_no_warn_when_at_least_one_policy(self, cli_runner):
        """Set firewall does not warn when at least one policy is assigned (DROP_ALL applies)."""
        ctx = create_mock_context()
        ctx.client.put.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55",
             "--rules", '{"copiedPolicies":[],"userPolicies":[{"id":42}],"active":true}'],
            ctx,
        )

        assert result.exit_code == 0
        assert "Warning" not in result.output

    @pytest.mark.parametrize("status_code", [401, 422, 500])
    def test_set_firewall_api_errors(self, cli_runner, status_code):
        """Set firewall exits with the HTTP status code on PUT API errors."""
        ctx = create_mock_context()
        ctx.client.put.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "set", "srv-12345", "00:11:22:33:44:55",
             "--rules", '{"copiedPolicies":[],"userPolicies":[{"id":42}],"active":true}'],
            ctx,
        )

        assert result.exit_code == status_code
        assert "Error:" in result.output


    def _setup_configure_ctx(self, list_response, firewall_response, policy_id=99):
        """Helper: configure mock context for the configure command."""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [list_response, firewall_response]
        ctx.client.post.return_value = {"id": policy_id, "name": "test", "rules": []}
        ctx.client.put.return_value = {}
        return ctx

    def test_configure_creates_policy_and_assigns(self, cli_runner):
        """Configure creates a new policy and assigns it to the interface."""
        ctx = self._setup_configure_ctx(
            FIREWALL_POLICY_LIST_EMPTY_RESPONSE, FIREWALL_GET_EMPTY
        )
        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "configure", "srv-12345", "00:11:22:33:44:55",
                 "--name", "test", "--rules", '{"rules":[]}'],
                ctx,
            )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "test" in result.output
        put_call = ctx.client.put.call_args
        assert put_call[0][0] == "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall"
        body = put_call[1]["json"]
        assert body["userPolicies"] == [{"id": 99}]
        assert body["active"] is True

    def test_configure_updates_existing_policy(self, cli_runner):
        """Configure updates an existing policy when the name already exists."""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [
            FIREWALL_POLICY_LIST_ONE_RESPONSE,
            FIREWALL_GET_EMPTY,
        ]
        ctx.client.put.return_value = {}

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "configure", "srv-12345", "00:11:22:33:44:55",
                 "--name", "my-policy", "--rules", '{"rules":[]}'],
                ctx,
            )

        assert result.exit_code == 0
        assert "42" in result.output
        # First PUT is the policy update; second PUT is the firewall assignment.
        assert ctx.client.put.call_count == 2

    def test_configure_preserves_copied_policies(self, cli_runner):
        """Configure keeps existing copiedPolicies when assigning the new user policy."""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [
            FIREWALL_POLICY_LIST_EMPTY_RESPONSE,
            FIREWALL_GET_WITH_COPIED,
        ]
        ctx.client.post.return_value = FIREWALL_POLICY_CREATE_RESPONSE
        ctx.client.put.return_value = {}

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "configure", "srv-12345", "00:11:22:33:44:55",
                 "--name", "new-policy"],
                ctx,
            )

        assert result.exit_code == 0
        body = ctx.client.put.call_args[1]["json"]
        assert body["copiedPolicies"] == [{"id": 10}]

    def test_configure_no_active_flag(self, cli_runner):
        """Configure passes active=False when --no-active is given."""
        ctx = create_mock_context()
        ctx.client.get.side_effect = [
            FIREWALL_POLICY_LIST_EMPTY_RESPONSE,
            FIREWALL_GET_EMPTY,
        ]
        ctx.client.post.return_value = FIREWALL_POLICY_CREATE_RESPONSE
        ctx.client.put.return_value = {}

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "configure", "srv-12345", "00:11:22:33:44:55",
                 "--name", "test", "--no-active"],
                ctx,
            )

        assert result.exit_code == 0
        body = ctx.client.put.call_args[1]["json"]
        assert body["active"] is False

    def test_configure_invalid_json(self, cli_runner):
        """Configure exits with code 1 when --rules contains invalid JSON."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_EMPTY_RESPONSE

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "configure", "srv-12345", "00:11:22:33:44:55",
                 "--name", "test", "--rules", "not-json"],
                ctx,
            )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.output

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_configure_api_errors(self, cli_runner, status_code):
        """Configure exits with the HTTP status code on API errors."""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Error", status_code=status_code)

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "configure", "srv-12345", "00:11:22:33:44:55", "--name", "test"],
                ctx,
            )

        assert result.exit_code == status_code
        assert "Error:" in result.output


    def test_reapply_firewall_success(self, cli_runner):
        """Reapply firewall succeeds."""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "reapply", "srv-12345", "00:11:22:33:44:55"],
            ctx,
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.post.assert_called_once_with(
            "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall:reapply"
        )

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_reapply_firewall_api_errors(self, cli_runner, status_code):
        """Reapply firewall exits with the HTTP status code on API errors."""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "reapply", "srv-12345", "00:11:22:33:44:55"],
            ctx,
        )

        assert result.exit_code == status_code


    def test_restore_firewall_success(self, cli_runner):
        """Restore firewall policies succeeds."""
        ctx = create_mock_context()
        ctx.client.post.return_value = {}

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "restore", "srv-12345", "00:11:22:33:44:55"],
            ctx,
        )

        assert result.exit_code == 0
        assert "[OK]" in result.output
        ctx.client.post.assert_called_once_with(
            "/api/v1/servers/srv-12345/interfaces/00:11:22:33:44:55/firewall:restore-copied-policies"
        )

    @pytest.mark.parametrize("status_code", [401, 404, 500])
    def test_restore_firewall_api_errors(self, cli_runner, status_code):
        """Restore firewall exits with the HTTP status code on API errors."""
        ctx = create_mock_context()
        ctx.client.post.side_effect = APIError("Error", status_code=status_code)

        result = invoke_with_mocks(
            cli_runner,
            ["firewall", "restore", "srv-12345", "00:11:22:33:44:55"],
            ctx,
        )

        assert result.exit_code == status_code


    def _setup_cleanup_ctx(self, all_policies, servers, interfaces_by_id, firewall_by_id_mac):
        """Build a mock context where get() dispatches based on the URL."""
        ctx = create_mock_context()

        def _get_dispatch(path, params=None):
            if path == "/api/v1/servers":
                return servers
            if path.endswith("/interfaces"):
                server_id = path.split("/")[4]
                return interfaces_by_id.get(server_id, [])
            if path.endswith("/firewall"):
                parts = path.split("/")
                server_id = parts[4]
                mac = parts[6]
                return firewall_by_id_mac.get((server_id, mac), FIREWALL_GET_EMPTY)
            if "firewall-policies" in path:
                return all_policies
            return []

        ctx.client.get.side_effect = _get_dispatch
        return ctx

    def test_cleanup_dry_run_shows_orphaned(self, cli_runner):
        """Cleanup with --dry-run lists orphaned policies without deleting."""
        ctx = self._setup_cleanup_ctx(
            all_policies=[{"id": 55, "name": "orphan"}],
            servers=[{"id": "srv-1"}],
            interfaces_by_id={"srv-1": [{"mac": "aa:bb:cc:dd:ee:ff"}]},
            firewall_by_id_mac={("srv-1", "aa:bb:cc:dd:ee:ff"): FIREWALL_GET_EMPTY},
        )

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "cleanup", "--dry-run"],
                ctx,
            )

        assert result.exit_code == 0
        assert "Would delete" in result.output
        assert "orphan" in result.output
        ctx.client.delete.assert_not_called()

    def test_cleanup_deletes_with_yes_flag(self, cli_runner):
        """Cleanup deletes orphaned policies when --yes is given."""
        ctx = self._setup_cleanup_ctx(
            all_policies=[{"id": 55, "name": "orphan"}],
            servers=[{"id": "srv-1"}],
            interfaces_by_id={"srv-1": [{"mac": "aa:bb:cc:dd:ee:ff"}]},
            firewall_by_id_mac={("srv-1", "aa:bb:cc:dd:ee:ff"): FIREWALL_GET_EMPTY},
        )
        ctx.client.delete.return_value = {}

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "cleanup", "--yes"],
                ctx,
            )

        assert result.exit_code == 0
        ctx.client.delete.assert_called_once_with(
            "/api/v1/users/user_123/firewall-policies/55"
        )

    def test_cleanup_skips_referenced_policies(self, cli_runner):
        """Cleanup does not delete policies that are assigned to at least one interface."""
        ctx = self._setup_cleanup_ctx(
            all_policies=[{"id": 42, "name": "in-use"}],
            servers=[{"id": "srv-1"}],
            interfaces_by_id={"srv-1": [{"mac": "aa:bb:cc:dd:ee:ff"}]},
            firewall_by_id_mac={
                ("srv-1", "aa:bb:cc:dd:ee:ff"): FIREWALL_GET_RESPONSE,  # userPolicies: [{id:42}]
            },
        )

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "cleanup", "--dry-run"],
                ctx,
            )

        assert result.exit_code == 0
        assert "No orphaned" in result.output
        ctx.client.delete.assert_not_called()

    def test_cleanup_nothing_to_delete(self, cli_runner):
        """Cleanup reports nothing to clean when all policies are in use."""
        ctx = self._setup_cleanup_ctx(
            all_policies=[],
            servers=[],
            interfaces_by_id={},
            firewall_by_id_mac={},
        )

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "cleanup", "--dry-run"],
                ctx,
            )

        assert result.exit_code == 0
        assert "No orphaned" in result.output

    def test_cleanup_interactive_abort(self, cli_runner):
        """Cleanup aborts when the user declines the confirmation prompt."""
        ctx = self._setup_cleanup_ctx(
            all_policies=[{"id": 55, "name": "orphan"}],
            servers=[{"id": "srv-1"}],
            interfaces_by_id={"srv-1": [{"mac": "aa:bb:cc:dd:ee:ff"}]},
            firewall_by_id_mac={("srv-1", "aa:bb:cc:dd:ee:ff"): FIREWALL_GET_EMPTY},
        )

        with patch(
            "netcupctl.commands.firewall.get_authenticated_user_id",
            return_value="user_123",
        ):
            result = invoke_with_mocks(
                cli_runner,
                ["firewall", "cleanup"],
                ctx,
                input="n\n",
            )

        assert result.exit_code == 1
        ctx.client.delete.assert_not_called()
