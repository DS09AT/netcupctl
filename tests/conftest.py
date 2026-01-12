import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timedelta
from click.testing import CliRunner

from netcupctl.config import ConfigManager
from netcupctl.auth import AuthManager
from netcupctl.client import NetcupClient
from netcupctl.output import OutputFormatter
from netcupctl.cli import cli, Context


@pytest.fixture
def temp_config_dir(tmp_path):
    return tmp_path / "netcupctl"


@pytest.fixture
def mock_config(temp_config_dir):
    config = ConfigManager()
    config.config_dir = temp_config_dir
    config.tokens_file = temp_config_dir / "tokens.json"
    config.config_file = temp_config_dir / "config.json"
    return config


@pytest.fixture
def valid_token_data():
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    return {
        "access_token": "test_access_token_12345",
        "refresh_token": "test_refresh_token_67890",
        "expires_at": expires_at,
        "user_id": "test_user_123",
    }


@pytest.fixture
def expired_token_data():
    expires_at = (datetime.now() - timedelta(hours=1)).isoformat()
    return {
        "access_token": "expired_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": expires_at,
        "user_id": "test_user_123",
    }


@pytest.fixture
def mock_auth(mock_config, valid_token_data):
    auth = AuthManager(config=mock_config)
    auth._token_data = valid_token_data
    return auth


@pytest.fixture
def mock_auth_unauthenticated(mock_config):
    auth = AuthManager(config=mock_config)
    auth._token_data = None
    return auth


@pytest.fixture
def mock_client(mock_auth, requests_mock):
    client = NetcupClient(auth=mock_auth)
    return client


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def mock_context(mock_config, mock_auth, mock_client):
    ctx = Context()
    ctx.config = mock_config
    ctx.auth = mock_auth
    ctx.client = mock_client
    ctx.formatter = OutputFormatter(format="json")
    return ctx


@pytest.fixture
def api_base_url():
    return "https://www.servercontrolpanel.de/scp-core"
