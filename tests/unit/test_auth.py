import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import requests

from netcupctl.auth import AuthManager, AuthError
from tests.fixtures.api_responses import (
    TOKEN_RESPONSE,
    USERINFO_RESPONSE,
    DEVICE_AUTH_RESPONSE,
    DEVICE_AUTH_ERROR_AUTHORIZATION_PENDING,
    DEVICE_AUTH_ERROR_SLOW_DOWN,
    DEVICE_AUTH_ERROR_ACCESS_DENIED,
    DEVICE_AUTH_ERROR_EXPIRED_TOKEN,
)


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

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_success(self, mock_sleep, mock_browser, mock_config, requests_mock):
        """Test successful device flow login"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)

        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = TOKEN_RESPONSE
        requests_mock.post(AuthManager.TOKEN_URL, [
            {"status_code": 200, "json": TOKEN_RESPONSE}
        ])

        requests_mock.get(AuthManager.USERINFO_URL, json=USERINFO_RESPONSE)

        auth = AuthManager(config=mock_config)
        result = auth.login()

        assert result is not None
        assert result["access_token"] == TOKEN_RESPONSE["access_token"]
        assert result["refresh_token"] == TOKEN_RESPONSE["refresh_token"]
        assert result["user_id"] == USERINFO_RESPONSE["id"]
        assert mock_browser.called

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_authorization_pending_then_success(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow with authorization_pending then success"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)

        requests_mock.post(AuthManager.TOKEN_URL, [
            {"status_code": 400, "json": DEVICE_AUTH_ERROR_AUTHORIZATION_PENDING},
            {"status_code": 200, "json": TOKEN_RESPONSE}
        ])

        requests_mock.get(AuthManager.USERINFO_URL, json=USERINFO_RESPONSE)

        auth = AuthManager(config=mock_config)
        result = auth.login()

        assert result is not None
        assert result["access_token"] == TOKEN_RESPONSE["access_token"]
        assert mock_sleep.call_count == 2

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_slow_down(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow handles slow_down response"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)

        requests_mock.post(AuthManager.TOKEN_URL, [
            {"status_code": 400, "json": DEVICE_AUTH_ERROR_SLOW_DOWN},
            {"status_code": 200, "json": TOKEN_RESPONSE}
        ])

        requests_mock.get(AuthManager.USERINFO_URL, json=USERINFO_RESPONSE)

        auth = AuthManager(config=mock_config)
        result = auth.login()

        assert result is not None
        assert mock_sleep.call_count == 2

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_access_denied(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow handles access denied"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)
        requests_mock.post(AuthManager.TOKEN_URL, status_code=400, json=DEVICE_AUTH_ERROR_ACCESS_DENIED)

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Authorization declined by user"):
            auth.login()

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_expired_token(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow handles expired token"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)
        requests_mock.post(AuthManager.TOKEN_URL, status_code=400, json=DEVICE_AUTH_ERROR_EXPIRED_TOKEN)

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Device code expired"):
            auth.login()

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_unknown_error(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow handles unknown error"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)
        requests_mock.post(AuthManager.TOKEN_URL, status_code=400, json={"error": "unknown_error"})

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Authentication error"):
            auth.login()

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_timeout(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow timeout after max attempts"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        device_response = DEVICE_AUTH_RESPONSE.copy()
        device_response["expires_in"] = 10
        device_response["interval"] = 5

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=device_response)
        requests_mock.post(AuthManager.TOKEN_URL, status_code=400, json=DEVICE_AUTH_ERROR_AUTHORIZATION_PENDING)

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Authentication timeout"):
            auth.login()

    @patch("webbrowser.open")
    def test_login_device_auth_request_fails(
        self, mock_browser, mock_config, requests_mock
    ):
        """Test device flow handles device auth request failure"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, exc=requests.ConnectionError)

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Failed to request device code"):
            auth.login()

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_polling_network_error(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow handles network error during polling"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)

        requests_mock.post(AuthManager.TOKEN_URL, exc=requests.ConnectionError)

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Failed to poll for token"):
            auth.login()

    @patch("webbrowser.open", side_effect=OSError("Browser not available"))
    @patch("time.sleep")
    def test_login_device_flow_browser_open_fails(
        self, mock_sleep, mock_browser, mock_config, requests_mock, capsys
    ):
        """Test device flow continues when browser open fails"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)
        requests_mock.post(AuthManager.TOKEN_URL, status_code=200, json=TOKEN_RESPONSE)
        requests_mock.get(AuthManager.USERINFO_URL, json=USERINFO_RESPONSE)

        auth = AuthManager(config=mock_config)
        result = auth.login()

        assert result is not None
        captured = capsys.readouterr()
        assert "Could not open browser automatically" in captured.out

    @patch("webbrowser.open")
    @patch("time.sleep")
    def test_login_device_flow_unexpected_status_code(
        self, mock_sleep, mock_browser, mock_config, requests_mock
    ):
        """Test device flow handles unexpected status codes"""
        mock_config.config_dir.mkdir(parents=True, exist_ok=True)

        requests_mock.post(AuthManager.DEVICE_AUTH_URL, json=DEVICE_AUTH_RESPONSE)
        requests_mock.post(AuthManager.TOKEN_URL, status_code=500)

        auth = AuthManager(config=mock_config)

        with pytest.raises(AuthError, match="Unexpected response: 500"):
            auth.login()

    def test_get_user_id_uses_sub_field_fallback(self, mock_config, requests_mock):
        """Test _get_user_id uses sub field when id field missing"""
        userinfo_with_sub_only = {"sub": "user_456", "email": "test@example.com"}
        requests_mock.get(AuthManager.USERINFO_URL, json=userinfo_with_sub_only)

        auth = AuthManager(config=mock_config)
        user_id = auth._get_user_id("test_token")

        assert user_id == "user_456"
