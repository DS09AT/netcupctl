import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from netcupctl.auth import AuthManager, AuthError
from tests.fixtures.api_responses import TOKEN_RESPONSE, USERINFO_RESPONSE


@pytest.mark.unit
class TestAuthManager:

    def test_init_with_config(self, mock_config):
        auth = AuthManager(config=mock_config)

        assert auth.config == mock_config
        assert auth._token_data is None

    def test_is_authenticated_with_tokens(self, mock_auth):
        assert mock_auth.is_authenticated() is True

    def test_is_authenticated_without_tokens(self, mock_auth_unauthenticated):
        assert mock_auth_unauthenticated.is_authenticated() is False

    def test_get_access_token_valid(self, mock_auth, valid_token_data):
        token = mock_auth.get_access_token()

        assert token == valid_token_data["access_token"]

    def test_get_access_token_no_tokens(self, mock_auth_unauthenticated):
        token = mock_auth_unauthenticated.get_access_token()

        assert token is None

    def test_get_access_token_expired_triggers_refresh(self, mock_config, expired_token_data, requests_mock):
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)
        mock_config.save_tokens(expired_token_data)

        requests_mock.post(
            AuthManager.TOKEN_URL,
            json=TOKEN_RESPONSE,
        )

        auth = AuthManager(config=mock_config)
        auth._token_data = expired_token_data
        token = auth.get_access_token()

        assert token == TOKEN_RESPONSE["access_token"]

    def test_get_token_info(self, mock_auth, valid_token_data):
        info = mock_auth.get_token_info()

        assert info is not None
        assert info["user_id"] == valid_token_data["user_id"]
        assert info["expires_at"] == valid_token_data["expires_at"]

    def test_get_token_info_no_tokens(self, mock_auth_unauthenticated):
        info = mock_auth_unauthenticated.get_token_info()

        assert info is None

    def test_logout_with_tokens(self, mock_config, valid_token_data, requests_mock):
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)
        mock_config.save_tokens(valid_token_data)

        requests_mock.post(AuthManager.REVOKE_URL, status_code=204)

        auth = AuthManager(config=mock_config)
        auth._token_data = valid_token_data
        result = auth.logout()

        assert result is True
        assert auth._token_data is None
        assert not mock_config.tokens_file.exists()

    def test_logout_without_tokens(self, mock_auth_unauthenticated):
        result = mock_auth_unauthenticated.logout()

        assert result is False

    def test_logout_revoke_fails_still_deletes_local(self, mock_config, valid_token_data, requests_mock):
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)
        mock_config.save_tokens(valid_token_data)

        requests_mock.post(AuthManager.REVOKE_URL, status_code=500)

        auth = AuthManager(config=mock_config)
        auth._token_data = valid_token_data
        result = auth.logout()

        assert result is True
        assert not mock_config.tokens_file.exists()

    def test_refresh_access_token_success(self, mock_config, expired_token_data, requests_mock):
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)
        mock_config.save_tokens(expired_token_data)

        requests_mock.post(AuthManager.TOKEN_URL, json=TOKEN_RESPONSE)

        auth = AuthManager(config=mock_config)
        auth._token_data = expired_token_data
        auth._refresh_access_token()

        assert auth._token_data["access_token"] == TOKEN_RESPONSE["access_token"]

    def test_refresh_access_token_no_tokens_raises(self, mock_auth_unauthenticated):
        with pytest.raises(AuthError, match="No tokens available"):
            mock_auth_unauthenticated._refresh_access_token()

    def test_refresh_access_token_no_refresh_token_raises(self, mock_config):
        auth = AuthManager(config=mock_config)
        auth._token_data = {"access_token": "test"}

        with pytest.raises(AuthError, match="No refresh token available"):
            auth._refresh_access_token()

    def test_refresh_access_token_network_error(self, mock_config, expired_token_data, requests_mock):
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        import requests
        requests_mock.post(AuthManager.TOKEN_URL, exc=requests.ConnectionError)

        auth = AuthManager(config=mock_config)
        auth._token_data = expired_token_data

        with pytest.raises(AuthError, match="Token refresh failed"):
            auth._refresh_access_token()

        assert auth._token_data is None

    def test_get_user_id(self, mock_config, requests_mock):
        requests_mock.get(AuthManager.USERINFO_URL, json=USERINFO_RESPONSE)

        auth = AuthManager(config=mock_config)
        user_id = auth._get_user_id("test_token")

        assert user_id == USERINFO_RESPONSE["id"]

    def test_get_user_id_network_error(self, mock_config, requests_mock):
        import requests
        requests_mock.get(AuthManager.USERINFO_URL, exc=requests.ConnectionError)

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Failed to get user info"):
            auth._get_user_id("test_token")

    def test_get_access_token_corrupted_expires_at(self, mock_config):
        auth = AuthManager(config=mock_config)
        auth._token_data = {
            "access_token": "test",
            "refresh_token": "test",
            "expires_at": "not-a-valid-datetime",
        }

        result = auth.get_access_token()

        assert result is None
        assert auth._token_data is None
