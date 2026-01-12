"""HTTP API client for netcup SCP REST API."""

import sys
from typing import Any, Dict, Optional

import requests

from netcupctl.auth import AuthManager


class APIError(Exception):
    """API error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
        """
        super().__init__(message)
        self.status_code = status_code


class NetcupClient:
    """Client for netcup SCP REST API."""

    BASE_URL = "https://www.servercontrolpanel.de/scp-core"

    def __init__(self, auth: AuthManager):
        """Initialize API client.

        Args:
            auth: Authentication manager
        """
        self.auth = auth
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "netcupctl/0.1.0",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: API path (e.g., /api/v1/servers)
            params: Query parameters
            json: JSON request body

        Returns:
            Response data as dictionary

        Raises:
            APIError: If request fails
            AuthError: If authentication fails
        """
        access_token = self.auth.get_access_token()
        if not access_token:
            print("Error: Not authenticated. Please run 'netcupctl auth login' first.", file=sys.stderr)
            sys.exit(1)

        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        if json is not None:
            if method.upper() == "PATCH":
                headers["Content-Type"] = "application/merge-patch+json"
            else:
                headers["Content-Type"] = "application/json"

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=30,
                verify=True,
            )

            if response.status_code in (200, 201, 202):
                if response.content:
                    try:
                        return response.json()
                    except requests.JSONDecodeError:
                        return {"data": response.text}
                else:
                    return {}

            elif response.status_code == 204:
                return {}

            elif response.status_code == 401:
                raise APIError("Authentication failed. Please login again.", status_code=401)

            elif response.status_code == 403:
                raise APIError("Access forbidden. You don't have permission for this operation.", status_code=403)

            elif response.status_code == 404:
                raise APIError("Resource not found.", status_code=404)

            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    error_msg = self._format_validation_error(error_data)
                except (ValueError, KeyError, requests.JSONDecodeError):
                    error_msg = "Validation error."
                raise APIError(error_msg, status_code=422)

            elif 400 <= response.status_code < 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_data.get("error", response.text))
                except (ValueError, KeyError, requests.JSONDecodeError):
                    error_msg = response.text or f"Client error (HTTP {response.status_code})"
                raise APIError(error_msg, status_code=response.status_code)

            elif 500 <= response.status_code < 600:
                msg = f"Server error (HTTP {response.status_code}). Please try again later."
                raise APIError(msg, status_code=response.status_code)

            else:
                raise APIError(f"Unexpected response (HTTP {response.status_code})", status_code=response.status_code)

        except requests.ConnectionError as exc:
            raise APIError(
                "Network error: Could not connect to API. Please check your internet connection."
            ) from exc

        except requests.Timeout as exc:
            raise APIError("Request timeout. The API did not respond in time.") from exc

        except requests.RequestException as exc:
            raise APIError(f"Request failed: {type(exc).__name__}") from exc

    def _format_validation_error(self, error_data: Dict[str, Any]) -> str:
        """Format validation error message.

        Args:
            error_data: Error response data

        Returns:
            Formatted error message
        """
        errors = error_data.get("errors", [])
        if errors:
            messages = []
            for error in errors:
                field = error.get("field", "unknown")
                message = error.get("message", "invalid")
                messages.append(f"  - {field}: {message}")
            return "Validation error:\n" + "\n".join(messages)

        return error_data.get("message", "Validation error")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request.

        Args:
            path: API path
            params: Query parameters

        Returns:
            Response data
        """
        return self.request("GET", path, params=params)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request.

        Args:
            path: API path
            json: JSON request body

        Returns:
            Response data
        """
        return self.request("POST", path, json=json)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request.

        Args:
            path: API path
            json: JSON request body

        Returns:
            Response data
        """
        return self.request("PUT", path, json=json)

    def patch(
        self, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make PATCH request.

        Args:
            path: API path
            params: Query parameters
            json: JSON request body

        Returns:
            Response data
        """
        return self.request("PATCH", path, params=params, json=json)

    def delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request.

        Args:
            path: API path

        Returns:
            Response data
        """
        return self.request("DELETE", path)

    def put_binary(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> Dict[str, Any]:
        """Make PUT request with binary data.

        Args:
            path: API path
            data: Binary data to upload
            content_type: Content type header

        Returns:
            Response data

        Raises:
            APIError: If request fails
        """
        access_token = self.auth.get_access_token()
        if not access_token:
            print("Error: Not authenticated. Please run 'netcupctl auth login' first.", file=sys.stderr)
            sys.exit(1)

        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": content_type,
        }

        try:
            response = self.session.put(
                url=url,
                headers=headers,
                data=data,
                timeout=300,  # Longer timeout for uploads
                verify=True,
            )

            if response.status_code in (200, 201, 202):
                if response.content:
                    try:
                        return response.json()
                    except requests.JSONDecodeError:
                        etag = response.headers.get("ETag", "")
                        return {"etag": etag, "data": response.text}
                else:
                    return {"etag": response.headers.get("ETag", "")}

            elif response.status_code == 204:
                return {"etag": response.headers.get("ETag", "")}

            elif response.status_code == 401:
                raise APIError("Authentication failed. Please login again.", status_code=401)

            elif response.status_code == 403:
                raise APIError("Access forbidden.", status_code=403)

            elif response.status_code == 404:
                raise APIError("Resource not found.", status_code=404)

            elif 400 <= response.status_code < 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_data.get("error", response.text))
                except (ValueError, KeyError, requests.JSONDecodeError):
                    error_msg = response.text or f"Client error (HTTP {response.status_code})"
                raise APIError(error_msg, status_code=response.status_code)

            elif 500 <= response.status_code < 600:
                raise APIError(f"Server error (HTTP {response.status_code})", status_code=response.status_code)

            else:
                raise APIError(f"Unexpected response (HTTP {response.status_code})", status_code=response.status_code)

        except requests.ConnectionError as exc:
            raise APIError("Network error: Could not connect to API.") from exc

        except requests.Timeout as exc:
            raise APIError("Request timeout during upload.") from exc

        except requests.RequestException as exc:
            raise APIError(f"Upload failed: {type(exc).__name__}") from exc
