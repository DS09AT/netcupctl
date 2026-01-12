import pytest
from unittest.mock import MagicMock, patch
import sys

from netcupctl.client import NetcupClient, APIError
from tests.fixtures.api_responses import (
    SERVER_LIST_RESPONSE,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
    ERROR_RESPONSE_500,
)


@pytest.mark.unit
class TestNetcupClient:

    def test_init(self, mock_auth):
        client = NetcupClient(auth=mock_auth)

        assert client.auth == mock_auth
        assert client.session is not None
        assert client.session.headers["User-Agent"] == "netcupctl/0.1.0"

    def test_get_success(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            json=SERVER_LIST_RESPONSE,
        )

        result = mock_client.get("/api/v1/servers")

        assert result == SERVER_LIST_RESPONSE

    def test_get_with_params(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            json=SERVER_LIST_RESPONSE,
        )

        result = mock_client.get("/api/v1/servers", params={"status": "running"})

        assert result == SERVER_LIST_RESPONSE
        assert requests_mock.last_request.qs == {"status": ["running"]}

    def test_post_success(self, mock_client, requests_mock, api_base_url):
        response_data = {"id": "new-server", "status": "creating"}
        requests_mock.post(
            f"{api_base_url}/api/v1/servers",
            json=response_data,
            status_code=201,
        )

        result = mock_client.post("/api/v1/servers", json={"name": "new-server"})

        assert result == response_data

    def test_put_success(self, mock_client, requests_mock, api_base_url):
        response_data = {"id": "srv-123", "name": "updated"}
        requests_mock.put(
            f"{api_base_url}/api/v1/servers/srv-123",
            json=response_data,
        )

        result = mock_client.put("/api/v1/servers/srv-123", json={"name": "updated"})

        assert result == response_data

    def test_patch_success(self, mock_client, requests_mock, api_base_url):
        response_data = {"id": "srv-123", "status": "updated"}
        requests_mock.patch(
            f"{api_base_url}/api/v1/servers/srv-123",
            json=response_data,
        )

        result = mock_client.patch("/api/v1/servers/srv-123", json={"status": "updated"})

        assert result == response_data

    def test_delete_success(self, mock_client, requests_mock, api_base_url):
        requests_mock.delete(
            f"{api_base_url}/api/v1/servers/srv-123",
            status_code=204,
        )

        result = mock_client.delete("/api/v1/servers/srv-123")

        assert result == {}

    def test_error_401_unauthorized(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            status_code=401,
            json=ERROR_RESPONSE_401,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/servers")

        assert exc_info.value.status_code == 401
        assert "Authentication failed" in str(exc_info.value)

    def test_error_403_forbidden(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            status_code=403,
            json=ERROR_RESPONSE_403,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/servers")

        assert exc_info.value.status_code == 403
        assert "forbidden" in str(exc_info.value).lower()

    def test_error_404_not_found(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers/nonexistent",
            status_code=404,
            json=ERROR_RESPONSE_404,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/servers/nonexistent")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()

    def test_error_422_validation(self, mock_client, requests_mock, api_base_url):
        requests_mock.post(
            f"{api_base_url}/api/v1/servers",
            status_code=422,
            json=ERROR_RESPONSE_422,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.post("/api/v1/servers", json={})

        assert exc_info.value.status_code == 422
        assert "Validation error" in str(exc_info.value)
        assert "name" in str(exc_info.value).lower()

    def test_error_500_server(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            status_code=500,
            json=ERROR_RESPONSE_500,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/servers")

        assert exc_info.value.status_code == 500
        assert "Server error" in str(exc_info.value)

    def test_connection_error(self, mock_client, requests_mock, api_base_url):
        import requests
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            exc=requests.ConnectionError,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/servers")

        assert "Network error" in str(exc_info.value)

    def test_timeout_error(self, mock_client, requests_mock, api_base_url):
        import requests
        requests_mock.get(
            f"{api_base_url}/api/v1/servers",
            exc=requests.Timeout,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/servers")

        assert "timeout" in str(exc_info.value).lower()

    def test_request_not_authenticated_exits(self, mock_auth_unauthenticated):
        client = NetcupClient(auth=mock_auth_unauthenticated)

        with pytest.raises(SystemExit) as exc_info:
            client.get("/api/v1/servers")

        assert exc_info.value.code == 1

    def test_put_binary_success(self, mock_client, requests_mock, api_base_url):
        requests_mock.put(
            f"{api_base_url}/api/v1/upload",
            status_code=200,
            headers={"ETag": '"abc123"'},
            text="",
        )

        result = mock_client.put_binary("/api/v1/upload", b"binary data")

        assert "etag" in result

    def test_put_binary_not_authenticated_exits(self, mock_auth_unauthenticated):
        client = NetcupClient(auth=mock_auth_unauthenticated)

        with pytest.raises(SystemExit) as exc_info:
            client.put_binary("/api/v1/upload", b"data")

        assert exc_info.value.code == 1

    def test_empty_response_body(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/empty",
            status_code=200,
            text="",
        )

        result = mock_client.get("/api/v1/empty")

        assert result == {}

    def test_non_json_response(self, mock_client, requests_mock, api_base_url):
        requests_mock.get(
            f"{api_base_url}/api/v1/ping",
            status_code=200,
            text="OK",
        )

        result = mock_client.get("/api/v1/ping")

        assert result == {"data": "OK"}

    def test_format_validation_error_with_errors_list(self, mock_client):
        error_data = {
            "errors": [
                {"field": "email", "message": "Invalid format"},
                {"field": "password", "message": "Too short"},
            ]
        }

        result = mock_client._format_validation_error(error_data)

        assert "email" in result
        assert "Invalid format" in result
        assert "password" in result

    def test_format_validation_error_with_message(self, mock_client):
        error_data = {"message": "Validation failed"}

        result = mock_client._format_validation_error(error_data)

        assert result == "Validation failed"

    def test_format_validation_error_empty(self, mock_client):
        error_data = {}

        result = mock_client._format_validation_error(error_data)

        assert result == "Validation error"

    @pytest.mark.parametrize("status_code", [400, 405, 409, 429])
    def test_other_4xx_errors(self, mock_client, requests_mock, api_base_url, status_code):
        requests_mock.get(
            f"{api_base_url}/api/v1/test",
            status_code=status_code,
            json={"message": "Client error"},
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/test")

        assert exc_info.value.status_code == status_code

    @pytest.mark.parametrize("status_code", [502, 503, 504])
    def test_other_5xx_errors(self, mock_client, requests_mock, api_base_url, status_code):
        requests_mock.get(
            f"{api_base_url}/api/v1/test",
            status_code=status_code,
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/api/v1/test")

        assert exc_info.value.status_code == status_code
        assert "Server error" in str(exc_info.value)
