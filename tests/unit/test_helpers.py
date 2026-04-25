"""Tests for netcupctl.commands.helpers — upsert_policy."""
import pytest
from unittest.mock import patch

from netcupctl.client import APIError
from netcupctl.commands.helpers import upsert_policy
from tests.fixtures.api_responses import (
    FIREWALL_POLICY_LIST_EMPTY_RESPONSE,
    FIREWALL_POLICY_LIST_ONE_RESPONSE,
    FIREWALL_POLICY_LIST_MULTIPLE_SAME_NAME,
    FIREWALL_POLICY_CREATE_RESPONSE,
    FIREWALL_POLICY_UPDATE_RESPONSE,
)
from tests.fixtures.cli_helpers import create_mock_context


@pytest.mark.unit
class TestUpsertPolicy:
    """Tests for the upsert_policy helper."""

    def test_creates_new_policy_when_none_found(self):
        """Creates a new policy when no exact name match exists."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_EMPTY_RESPONSE
        ctx.client.post.return_value = FIREWALL_POLICY_CREATE_RESPONSE

        result = upsert_policy(ctx, "user_123", "new-policy", {"rules": []})

        assert result == 99
        ctx.client.post.assert_called_once_with(
            "/api/v1/users/user_123/firewall-policies",
            json={"name": "new-policy", "rules": []},
        )
        ctx.client.put.assert_not_called()

    def test_updates_existing_policy_when_one_match_found(self):
        """Updates the matching policy in place when exactly one exact name is found."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_ONE_RESPONSE
        ctx.client.put.return_value = FIREWALL_POLICY_UPDATE_RESPONSE

        result = upsert_policy(ctx, "user_123", "my-policy", {"rules": []})

        assert result == 42
        ctx.client.put.assert_called_once_with(
            "/api/v1/users/user_123/firewall-policies/42",
            json={"name": "my-policy", "rules": []},
        )
        ctx.client.post.assert_not_called()

    def test_raises_on_multiple_name_matches(self):
        """Raises APIError when more than one policy shares the given name."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_MULTIPLE_SAME_NAME

        with pytest.raises(APIError, match="Multiple policies named 'my-policy'"):
            upsert_policy(ctx, "user_123", "my-policy", {})

        ctx.client.post.assert_not_called()
        ctx.client.put.assert_not_called()

    def test_search_uses_q_param_and_limit(self):
        """Passes the name as the q search parameter with a limit of 100."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_EMPTY_RESPONSE
        ctx.client.post.return_value = FIREWALL_POLICY_CREATE_RESPONSE

        upsert_policy(ctx, "user_123", "find-me", {})

        ctx.client.get.assert_called_once_with(
            "/api/v1/users/user_123/firewall-policies",
            params={"q": "find-me", "limit": 100},
        )

    def test_ignores_partial_name_matches(self):
        """Does not treat partial matches from the API search as exact matches."""
        ctx = create_mock_context()
        # API returns a policy whose name contains the search term but is not identical.
        ctx.client.get.return_value = [
            {"id": 77, "name": "my-policy-extended", "rules": []},
        ]
        ctx.client.post.return_value = FIREWALL_POLICY_CREATE_RESPONSE

        result = upsert_policy(ctx, "user_123", "my-policy", {})

        assert result == 99
        ctx.client.post.assert_called_once()

    def test_api_error_on_get_propagates(self):
        """Propagates APIError from the list call."""
        ctx = create_mock_context()
        ctx.client.get.side_effect = APIError("Server error", status_code=500)

        with pytest.raises(APIError):
            upsert_policy(ctx, "user_123", "any", {})

    def test_api_error_on_post_propagates(self):
        """Propagates APIError from the create call."""
        ctx = create_mock_context()
        ctx.client.get.return_value = FIREWALL_POLICY_LIST_EMPTY_RESPONSE
        ctx.client.post.side_effect = APIError("Validation error", status_code=422)

        with pytest.raises(APIError):
            upsert_policy(ctx, "user_123", "bad-policy", {})
