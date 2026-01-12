"""
Tests for netcupctl.spec_manager
"""
import json
import copy
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

from netcupctl.spec_manager import SpecManager, SpecError
from tests.fixtures.api_responses import (
    OPENAPI_SPEC_RESPONSE,
    OPENAPI_SPEC_INVALID_RESPONSE,
)


@pytest.mark.unit
class TestSpecManager:
    """Test suite for OpenAPI specification manager"""

    # Initialization tests
    def test_init_valid_path(self, temp_data_dir):
        """Test initialization with valid data directory"""
        manager = SpecManager(temp_data_dir)
        assert manager.data_dir == temp_data_dir.resolve()
        assert manager.spec_file == (temp_data_dir / "openapi.json").resolve()

    def test_init_path_traversal_detected(self, tmp_path):
        """Test initialization rejects path traversal attempts"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.side_effect = [
                data_dir,
                tmp_path.parent / "etc" / "passwd"
            ]
            with pytest.raises(SpecError, match="path traversal detected"):
                SpecManager(data_dir)

    # get_local_version tests
    def test_get_local_version_file_not_exists(self, temp_data_dir):
        """Test get_local_version when file doesn't exist"""
        manager = SpecManager(temp_data_dir)
        assert manager.get_local_version() is None

    def test_get_local_version_valid_file(self, temp_data_dir):
        """Test get_local_version with valid OpenAPI file"""
        manager = SpecManager(temp_data_dir)
        spec_file = temp_data_dir / "openapi.json"
        spec_file.write_text(json.dumps(OPENAPI_SPEC_RESPONSE), encoding="utf-8")

        version = manager.get_local_version()
        assert version == "1.2.3"

    def test_get_local_version_malformed_json(self, temp_data_dir):
        """Test get_local_version with malformed JSON"""
        manager = SpecManager(temp_data_dir)
        spec_file = temp_data_dir / "openapi.json"
        spec_file.write_text(OPENAPI_SPEC_INVALID_RESPONSE, encoding="utf-8")

        version = manager.get_local_version()
        assert version is None

    def test_get_local_version_oversized_file(self, temp_data_dir):
        """Test get_local_version rejects files > 10MB"""
        manager = SpecManager(temp_data_dir)
        spec_file = temp_data_dir / "openapi.json"

        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 11 * 1024 * 1024
            version = manager.get_local_version()
            assert version is None

    def test_get_local_version_missing_version_field(self, temp_data_dir):
        """Test get_local_version when spec missing version field"""
        manager = SpecManager(temp_data_dir)
        spec_file = temp_data_dir / "openapi.json"
        invalid_spec = {"openapi": "3.0.0", "info": {"title": "Test"}}
        spec_file.write_text(json.dumps(invalid_spec), encoding="utf-8")

        version = manager.get_local_version()
        assert version is None

    def test_get_local_version_empty_version(self, temp_data_dir):
        """Test get_local_version when version field is empty"""
        manager = SpecManager(temp_data_dir)
        spec_file = temp_data_dir / "openapi.json"
        invalid_spec = {"openapi": "3.0.0", "info": {"version": ""}}
        spec_file.write_text(json.dumps(invalid_spec), encoding="utf-8")

        version = manager.get_local_version()
        assert version is None

    def test_get_local_version_os_error(self, temp_data_dir):
        """Test get_local_version handles OSError gracefully"""
        manager = SpecManager(temp_data_dir)
        spec_file = temp_data_dir / "openapi.json"
        spec_file.write_text("{}", encoding="utf-8")

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            version = manager.get_local_version()
            assert version is None

    # download_spec tests
    @patch("requests.get")
    def test_download_spec_success(self, mock_get, temp_data_dir):
        """Test successful spec download"""
        mock_response = Mock()
        mock_response.json.return_value = OPENAPI_SPEC_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = SpecManager(temp_data_dir)
        spec = manager.download_spec()

        assert spec == OPENAPI_SPEC_RESPONSE
        mock_get.assert_called_once_with(
            "https://servercontrolpanel.de/scp-core/api/v1/openapi",
            timeout=30,
            verify=True
        )

    @patch("requests.get")
    def test_download_spec_connection_error(self, mock_get, temp_data_dir):
        """Test download_spec handles connection errors"""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="Failed to download OpenAPI spec"):
            manager.download_spec()

    @patch("requests.get")
    def test_download_spec_timeout(self, mock_get, temp_data_dir):
        """Test download_spec handles timeout"""
        mock_get.side_effect = requests.Timeout("Request timeout")

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="Failed to download OpenAPI spec"):
            manager.download_spec()

    @patch("requests.get")
    def test_download_spec_http_error(self, mock_get, temp_data_dir):
        """Test download_spec handles HTTP errors"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="Failed to download OpenAPI spec"):
            manager.download_spec()

    @patch("requests.get")
    def test_download_spec_invalid_json(self, mock_get, temp_data_dir):
        """Test download_spec handles invalid JSON response"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="Invalid OpenAPI spec format"):
            manager.download_spec()

    @patch("requests.get")
    def test_download_spec_not_json_object(self, mock_get, temp_data_dir):
        """Test download_spec rejects non-dict responses"""
        mock_response = Mock()
        mock_response.json.return_value = ["not", "an", "object"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="expected JSON object"):
            manager.download_spec()

    @patch("requests.get")
    def test_download_spec_missing_openapi_field(self, mock_get, temp_data_dir):
        """Test download_spec rejects spec without openapi/swagger field"""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "1.0.0"}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="not an OpenAPI specification"):
            manager.download_spec()

    @patch("requests.get")
    def test_download_spec_missing_info_field(self, mock_get, temp_data_dir):
        """Test download_spec rejects spec without info field"""
        mock_response = Mock()
        mock_response.json.return_value = {"openapi": "3.0.0"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="missing 'info' field"):
            manager.download_spec()

    # get_remote_version tests
    def test_get_remote_version_success(self, temp_data_dir):
        """Test get_remote_version extracts version correctly"""
        manager = SpecManager(temp_data_dir)
        version = manager.get_remote_version(OPENAPI_SPEC_RESPONSE)
        assert version == "1.2.3"

    def test_get_remote_version_missing_info(self, temp_data_dir):
        """Test get_remote_version fails when info field missing"""
        manager = SpecManager(temp_data_dir)
        spec = {"openapi": "3.0.0"}

        with pytest.raises(SpecError, match="Missing 'info.version' field"):
            manager.get_remote_version(spec)

    def test_get_remote_version_missing_version(self, temp_data_dir):
        """Test get_remote_version fails when version field missing"""
        manager = SpecManager(temp_data_dir)
        spec = {"openapi": "3.0.0", "info": {"title": "Test"}}

        with pytest.raises(SpecError, match="Missing 'info.version' field"):
            manager.get_remote_version(spec)

    def test_get_remote_version_empty_version(self, temp_data_dir):
        """Test get_remote_version fails when version is empty"""
        manager = SpecManager(temp_data_dir)
        spec = {"openapi": "3.0.0", "info": {"version": ""}}

        with pytest.raises(SpecError, match="Version field is empty"):
            manager.get_remote_version(spec)

    # save_spec tests
    def test_save_spec_success(self, temp_data_dir):
        """Test save_spec saves file atomically"""
        manager = SpecManager(temp_data_dir)
        manager.save_spec(OPENAPI_SPEC_RESPONSE)

        assert manager.spec_file.exists()
        with open(manager.spec_file, "r", encoding="utf-8") as f:
            saved_spec = json.load(f)
        assert saved_spec == OPENAPI_SPEC_RESPONSE

    def test_save_spec_creates_directory(self, tmp_path):
        """Test save_spec creates data directory if missing"""
        data_dir = tmp_path / "nonexistent" / "data"
        manager = SpecManager(data_dir)
        manager.save_spec(OPENAPI_SPEC_RESPONSE)

        assert data_dir.exists()
        assert manager.spec_file.exists()

    def test_save_spec_invalid_data_type(self, temp_data_dir):
        """Test save_spec rejects non-dict data"""
        manager = SpecManager(temp_data_dir)

        with pytest.raises(SpecError, match="must be a dictionary"):
            manager.save_spec("not a dict")

    def test_save_spec_exceeds_size_limit(self, temp_data_dir):
        """Test save_spec rejects specs exceeding size limit"""
        manager = SpecManager(temp_data_dir)
        huge_spec = {
            "openapi": "3.0.0",
            "info": {"version": "1.0.0"},
            "paths": {"x" * (11 * 1024 * 1024): {}}
        }

        with pytest.raises(SpecError, match="exceeds maximum allowed size"):
            manager.save_spec(huge_spec)

    def test_save_spec_write_error(self, temp_data_dir):
        """Test save_spec handles write errors"""
        manager = SpecManager(temp_data_dir)

        with patch("builtins.open", side_effect=OSError("Disk full")):
            with pytest.raises(SpecError, match="Failed to save OpenAPI spec"):
                manager.save_spec(OPENAPI_SPEC_RESPONSE)

    def test_save_spec_cleans_up_temp_file_on_error(self, temp_data_dir):
        """Test save_spec removes temp file after write error"""
        manager = SpecManager(temp_data_dir)
        temp_file = temp_data_dir / "openapi.tmp"

        with patch("builtins.open") as mock_open:
            mock_open.side_effect = [
                MagicMock(__enter__=Mock(side_effect=OSError("Write error")))
            ]
            try:
                manager.save_spec(OPENAPI_SPEC_RESPONSE)
            except SpecError:
                pass

            assert not temp_file.exists()

    # update_spec tests
    @patch.object(SpecManager, "download_spec")
    def test_update_spec_first_download(self, mock_download, temp_data_dir):
        """Test update_spec performs first download when no local spec exists"""
        mock_download.return_value = OPENAPI_SPEC_RESPONSE

        manager = SpecManager(temp_data_dir)
        result = manager.update_spec()

        assert result["status"] == "first_download"
        assert result["local_version"] is None
        assert result["remote_version"] == "1.2.3"
        assert manager.spec_file.exists()

    @patch.object(SpecManager, "download_spec")
    def test_update_spec_updated(self, mock_download, temp_data_dir):
        """Test update_spec downloads when versions differ"""
        old_spec = copy.deepcopy(OPENAPI_SPEC_RESPONSE)
        old_spec["info"]["version"] = "1.0.0"

        spec_file = temp_data_dir / "openapi.json"
        spec_file.write_text(json.dumps(old_spec), encoding="utf-8")

        mock_download.return_value = OPENAPI_SPEC_RESPONSE

        manager = SpecManager(temp_data_dir)
        result = manager.update_spec()

        assert result["status"] == "updated"
        assert result["local_version"] == "1.0.0"
        assert result["remote_version"] == "1.2.3"

    @patch.object(SpecManager, "download_spec")
    def test_update_spec_up_to_date(self, mock_download, temp_data_dir):
        """Test update_spec skips download when versions match"""
        spec_file = temp_data_dir / "openapi.json"
        spec_file.write_text(json.dumps(OPENAPI_SPEC_RESPONSE), encoding="utf-8")

        mock_download.return_value = OPENAPI_SPEC_RESPONSE

        manager = SpecManager(temp_data_dir)
        result = manager.update_spec()

        assert result["status"] == "up_to_date"
        assert result["local_version"] == "1.2.3"
        assert result["remote_version"] == "1.2.3"

    @patch.object(SpecManager, "download_spec")
    def test_update_spec_download_fails(self, mock_download, temp_data_dir):
        """Test update_spec propagates download errors"""
        mock_download.side_effect = SpecError("Network error")

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="Network error"):
            manager.update_spec()

    @patch.object(SpecManager, "download_spec")
    @patch.object(SpecManager, "save_spec")
    def test_update_spec_save_fails(self, mock_save, mock_download, temp_data_dir):
        """Test update_spec propagates save errors"""
        mock_download.return_value = OPENAPI_SPEC_RESPONSE
        mock_save.side_effect = SpecError("Disk full")

        manager = SpecManager(temp_data_dir)
        with pytest.raises(SpecError, match="Disk full"):
            manager.update_spec()
