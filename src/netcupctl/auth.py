"""OAuth2 authentication management for netcupctl."""

import time
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, Optional

import requests

from netcupctl.config import ConfigManager


class AuthError(Exception):
    """Authentication error."""

    pass


class AuthManager:
    """Manages OAuth2 Device Flow authentication."""

    DEVICE_AUTH_URL = "https://www.servercontrolpanel.de/realms/scp/protocol/openid-connect/auth/device"
    TOKEN_URL = "https://www.servercontrolpanel.de/realms/scp/protocol/openid-connect/token"
    REVOKE_URL = "https://www.servercontrolpanel.de/realms/scp/protocol/openid-connect/revoke"
    USERINFO_URL = "https://www.servercontrolpanel.de/realms/scp/protocol/openid-connect/userinfo"
    CLIENT_ID = "scp"

    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize authentication manager.

        Args:
            config: Configuration manager (creates new one if not provided)
        """
        self.config = config or ConfigManager()
        self._token_data: Optional[Dict] = None

    def login(self) -> Dict[str, str]:
        """Perform OAuth2 Device Flow login.

        Returns:
            Dictionary with access_token, refresh_token, user_id, expires_at

        Raises:
            AuthError: If login fails
        """
        try:
            response = requests.post(
                self.DEVICE_AUTH_URL,
                data={"client_id": self.CLIENT_ID, "scope": "offline_access openid"},
                timeout=30,
                verify=True,
            )
            response.raise_for_status()
            device_data = response.json()
        except requests.RequestException as e:
            raise AuthError(f"Failed to request device code: {type(e).__name__}")

        device_code = device_data["device_code"]
        verification_uri = device_data["verification_uri_complete"]
        interval = device_data.get("interval", 5)
        expires_in = device_data["expires_in"]

        print(f"\nPlease open the following URL in your browser:")
        print(f"\n  {verification_uri}\n")

        try:
            webbrowser.open(verification_uri)
            print("Browser opened automatically. Please complete authentication.")
        except Exception:
            # browser open may fail on headless systems or restricted environments
            print("Could not open browser automatically. Please open the URL manually.")

        print(f"\nWaiting for authentication (timeout: {expires_in} seconds)...\n")
        max_attempts = expires_in // interval
        for attempt in range(max_attempts):
            time.sleep(interval)

            try:
                response = requests.post(
                    self.TOKEN_URL,
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "device_code": device_code,
                        "client_id": self.CLIENT_ID,
                    },
                    timeout=30,
                    verify=True,
                )

                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data["access_token"]
                    refresh_token = token_data["refresh_token"]
                    expires_in = token_data["expires_in"]

                    user_id = self._get_user_id(access_token)
                    expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

                    tokens = {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_at": expires_at,
                        "user_id": user_id,
                    }
                    self.config.save_tokens(tokens)
                    self._token_data = tokens

                    return tokens

                elif response.status_code == 400:
                    error_data = response.json()
                    error = error_data.get("error", "unknown")

                    if error == "authorization_pending":
                        print(f"  Polling... (attempt {attempt + 1}/{max_attempts})", end="\r", flush=True)
                        continue
                    elif error == "slow_down":
                        # OAuth server requests increased polling interval
                        interval += 5
                        continue
                    elif error == "access_denied":
                        raise AuthError("Authorization declined by user")
                    elif error == "expired_token":
                        raise AuthError("Device code expired. Please try again.")
                    else:
                        raise AuthError(f"Authentication error: {error}")
                else:
                    raise AuthError(f"Unexpected response: {response.status_code}")

            except requests.RequestException as e:
                raise AuthError(f"Failed to poll for token: {type(e).__name__}")

        raise AuthError("Authentication timeout. Please try again.")

    def _get_user_id(self, access_token: str) -> str:
        """Get user ID from userinfo endpoint.

        Args:
            access_token: Valid access token

        Returns:
            User ID

        Raises:
            AuthError: If request fails
        """
        try:
            response = requests.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30,
                verify=True,
            )
            response.raise_for_status()
            userinfo = response.json()
            return userinfo.get("id", userinfo.get("sub", "unknown"))
        except requests.RequestException:
            raise AuthError("Failed to get user info")

    def logout(self) -> bool:
        """Logout and revoke tokens.

        Returns:
            True if logout successful, False if no tokens found

        Raises:
            AuthError: If revocation fails
        """
        tokens = self.config.load_tokens()
        if not tokens:
            return False

        refresh_token = tokens.get("refresh_token")

        if refresh_token:
            try:
                response = requests.post(
                    self.REVOKE_URL,
                    data={
                        "client_id": self.CLIENT_ID,
                        "token": refresh_token,
                        "token_type_hint": "refresh_token",
                    },
                    timeout=30,
                    verify=True,
                )
                # server returns 204 on success, but may also return 200
                if response.status_code not in (200, 204):
                    print(f"Warning: Token revocation returned status {response.status_code}")
            except requests.RequestException as e:
                print(f"Warning: Failed to revoke token at server: {e}")

        self.config.delete_tokens()
        self._token_data = None
        return True

    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if necessary.

        Returns:
            Access token or None if not authenticated

        Raises:
            AuthError: If refresh fails
        """
        if self._token_data is None:
            self._token_data = self.config.load_tokens()

        if not self._token_data:
            return None

        # refresh token if it expires within 60 seconds
        try:
            expires_at = datetime.fromisoformat(self._token_data["expires_at"])
        except (ValueError, TypeError):
            # corrupted expires_at, delete tokens and require re-login
            self._token_data = None
            self.config.delete_tokens()
            return None

        if datetime.now() >= expires_at - timedelta(seconds=60):
            self._refresh_access_token()

        return self._token_data["access_token"]

    def _refresh_access_token(self) -> None:
        """Refresh access token using refresh token.

        Raises:
            AuthError: If refresh fails
        """
        if not self._token_data:
            raise AuthError("No tokens available")

        refresh_token = self._token_data.get("refresh_token")
        if not refresh_token:
            raise AuthError("No refresh token available")

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.CLIENT_ID,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=30,
                verify=True,
            )
            response.raise_for_status()
            token_data = response.json()

            access_token = token_data["access_token"]
            new_refresh_token = token_data.get("refresh_token", refresh_token)
            expires_in = token_data["expires_in"]

            expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

            self._token_data["access_token"] = access_token
            self._token_data["refresh_token"] = new_refresh_token
            self._token_data["expires_at"] = expires_at

            self.config.save_tokens(self._token_data)

        except requests.RequestException:
            self._token_data = None
            self.config.delete_tokens()
            raise AuthError("Token refresh failed. Please login again.")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.

        Returns:
            True if valid tokens exist, False otherwise
        """
        if self._token_data is None:
            self._token_data = self.config.load_tokens()

        return self._token_data is not None

    def get_token_info(self) -> Optional[Dict[str, str]]:
        """Get information about current tokens.

        Returns:
            Dictionary with user_id, expires_at, or None if not authenticated
        """
        if self._token_data is None:
            self._token_data = self.config.load_tokens()

        if not self._token_data:
            return None

        return {
            "user_id": self._token_data.get("user_id", "unknown"),
            "expires_at": self._token_data.get("expires_at", "unknown"),
        }
