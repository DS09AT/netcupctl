from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from netcupctl.cli import cli, Context
from netcupctl.config import ConfigManager
from netcupctl.auth import AuthManager
from netcupctl.client import NetcupClient
from netcupctl.output import OutputFormatter


def create_mock_context(
    authenticated=True,
    token_data=None,
    output_format="json",
):
    config = MagicMock(spec=ConfigManager)
    auth = MagicMock(spec=AuthManager)
    client = MagicMock(spec=NetcupClient)

    if authenticated:
        auth.is_authenticated.return_value = True
        auth.get_access_token.return_value = "test_access_token"
        if token_data:
            auth.get_token_info.return_value = token_data
        else:
            auth.get_token_info.return_value = {
                "user_id": "test_user_123",
                "expires_at": "2099-12-31T23:59:59",
            }
    else:
        auth.is_authenticated.return_value = False
        auth.get_access_token.return_value = None
        auth.get_token_info.return_value = None

    ctx = Context.__new__(Context)
    ctx.config = config
    ctx.auth = auth
    ctx.client = client
    ctx.formatter = OutputFormatter(format=output_format)

    return ctx


def invoke_with_mocks(runner, args, mock_ctx, input=None, catch_exceptions=True):
    with patch.object(Context, '__init__', lambda self: None):
        with patch('netcupctl.cli.Context') as MockContext:
            MockContext.return_value = mock_ctx
            with patch('netcupctl.cli.NetcupClient') as MockClient:
                MockClient.return_value = mock_ctx.client
                return runner.invoke(
                    cli,
                    args,
                    input=input,
                    catch_exceptions=catch_exceptions,
                )


def setup_mock_api_response(requests_mock, base_url, method, path, json=None, status_code=200, text=None):
    url = f"{base_url}{path}"
    mock_method = getattr(requests_mock, method.lower())

    kwargs = {"status_code": status_code}
    if json is not None:
        kwargs["json"] = json
    elif text is not None:
        kwargs["text"] = text

    return mock_method(url, **kwargs)
