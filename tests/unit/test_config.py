import pytest
import json
from pathlib import Path

from netcupctl.config import ConfigManager


@pytest.mark.unit
class TestConfigManager:

    def test_config_dir_creation(self, temp_config_dir):
        config = ConfigManager()
        config.config_dir = temp_config_dir
        config.ensure_config_dir()

        assert temp_config_dir.exists()
        assert temp_config_dir.is_dir()

    def test_save_and_load_json(self, mock_config):
        test_data = {"key": "value", "number": 42}
        test_file = mock_config.config_dir / "test.json"

        mock_config.save_json(test_file, test_data)
        loaded = mock_config.load_json(test_file)

        assert loaded == test_data

    def test_load_json_nonexistent_file(self, mock_config):
        nonexistent = mock_config.config_dir / "nonexistent.json"

        result = mock_config.load_json(nonexistent)

        assert result is None

    def test_load_json_invalid_json(self, mock_config, temp_config_dir):
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        invalid_file = temp_config_dir / "invalid.json"
        invalid_file.write_text("not valid json {{{")

        result = mock_config.load_json(invalid_file)

        assert result is None

    def test_save_tokens(self, mock_config, valid_token_data):
        mock_config.save_tokens(valid_token_data)

        assert mock_config.tokens_file.exists()

        loaded = mock_config.load_tokens()
        assert loaded["access_token"] == valid_token_data["access_token"]
        assert loaded["refresh_token"] == valid_token_data["refresh_token"]

    def test_load_tokens_validates_required_fields(self, mock_config, temp_config_dir):
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        incomplete_tokens = {"access_token": "token"}
        mock_config.save_json(mock_config.tokens_file, incomplete_tokens)

        result = mock_config.load_tokens()

        assert result is None
        assert not mock_config.tokens_file.exists()

    def test_delete_tokens(self, mock_config, valid_token_data):
        mock_config.save_tokens(valid_token_data)
        assert mock_config.tokens_file.exists()

        result = mock_config.delete_tokens()

        assert result is True
        assert not mock_config.tokens_file.exists()

    def test_delete_tokens_nonexistent(self, mock_config):
        result = mock_config.delete_tokens()

        assert result is False

    def test_load_config_empty(self, mock_config):
        result = mock_config.load_config()

        assert result == {}

    def test_save_and_load_config(self, mock_config):
        test_config = {"setting1": "value1", "setting2": True}

        mock_config.save_config(test_config)
        loaded = mock_config.load_config()

        assert loaded == test_config

    def test_delete_file(self, mock_config, temp_config_dir):
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        test_file = temp_config_dir / "deleteme.txt"
        test_file.write_text("test")

        result = mock_config.delete_file(test_file)

        assert result is True
        assert not test_file.exists()

    def test_delete_file_nonexistent(self, mock_config, temp_config_dir):
        nonexistent = temp_config_dir / "nonexistent.txt"

        result = mock_config.delete_file(nonexistent)

        assert result is False

    @pytest.mark.parametrize("token_data,expected_valid", [
        ({"access_token": "a", "refresh_token": "r", "expires_at": "2099-01-01"}, True),
        ({"access_token": "", "refresh_token": "r", "expires_at": "2099-01-01"}, False),
        ({"access_token": "a", "refresh_token": "", "expires_at": "2099-01-01"}, False),
        ({"access_token": "a", "refresh_token": "r", "expires_at": ""}, False),
        ({"access_token": "a", "refresh_token": "r"}, False),
        ({}, False),
    ])
    def test_load_tokens_validation(self, mock_config, temp_config_dir, token_data, expected_valid):
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        mock_config.save_json(mock_config.tokens_file, token_data)

        result = mock_config.load_tokens()

        if expected_valid:
            assert result is not None
        else:
            assert result is None
