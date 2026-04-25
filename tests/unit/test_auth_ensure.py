"""Tests for the 'netcupctl auth ensure' command."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from netcupctl.client import APIError
from tests.fixtures.cli_helpers import create_mock_context, invoke_with_mocks


@pytest.mark.unit
class TestAuthEnsure:
    """Tests for the auth ensure command."""

    def _ctx_with_ttl(self, ttl_seconds: int, authenticated: bool = True):
        """Build a mock context whose token expires in ttl_seconds."""
        ctx = create_mock_context(authenticated=authenticated)
        expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
        ctx.auth.get_token_info.return_value = {
            "user_id": "test_user_123",
            "expires_at": expires_at,
        }
        return ctx

    def test_ensure_exits_0_when_token_valid(self, cli_runner):
        """Exits 0 and prints the TTL when the token is valid."""
        ctx = self._ctx_with_ttl(3600)

        result = invoke_with_mocks(cli_runner, ["auth", "ensure"], ctx)

        assert result.exit_code == 0
        assert "[OK]" in result.output
        assert "Token valid for" in result.output

    def test_ensure_refreshes_when_ttl_below_min(self, cli_runner):
        """Refreshes the token when remaining TTL is below --min-ttl."""
        ctx = self._ctx_with_ttl(10)  # 10s < default 300s
        ctx.auth.get_access_token.return_value = "new_token"
        # After refresh, return a token valid for 3600s.
        refreshed_expires = (datetime.now() + timedelta(seconds=3600)).isoformat()
        ctx.auth.get_token_info.side_effect = [
            {"user_id": "test_user_123", "expires_at": (datetime.now() + timedelta(seconds=10)).isoformat()},
            {"user_id": "test_user_123", "expires_at": refreshed_expires},
        ]

        result = invoke_with_mocks(cli_runner, ["auth", "ensure"], ctx)

        assert result.exit_code == 0
        ctx.auth.get_access_token.assert_called_once()
        assert "[OK]" in result.output

    def test_ensure_exits_1_when_not_authenticated(self, cli_runner):
        """Exits 1 with an error message when not authenticated."""
        ctx = create_mock_context(authenticated=False)

        result = invoke_with_mocks(cli_runner, ["auth", "ensure"], ctx)

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_ensure_respects_custom_min_ttl(self, cli_runner):
        """Does not refresh when TTL exceeds a custom --min-ttl."""
        ctx = self._ctx_with_ttl(200)  # 200s > 60s custom min

        result = invoke_with_mocks(
            cli_runner, ["auth", "ensure", "--min-ttl", "60"], ctx
        )

        assert result.exit_code == 0
        ctx.auth.get_access_token.assert_not_called()
