"""OpenAPI specification management for netcupctl."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import requests


class SpecError(Exception):
    """Specification management error."""

    pass


class SpecManager:
    """Manages OpenAPI specification download and updates."""

    OPENAPI_URL = "https://servercontrolpanel.de/scp-core/api/v1/openapi"
    MAX_SPEC_SIZE = 10 * 1024 * 1024
    SPEC_FILENAME = "openapi.json"

    def __init__(self, data_dir: Path):
        """Initialize spec manager.

        Args:
            data_dir: Path to data directory where spec file is stored
        """
        self.data_dir = data_dir.resolve()
        self.spec_file = (data_dir / self.SPEC_FILENAME).resolve()

        if not str(self.spec_file).startswith(str(self.data_dir)):
            raise SpecError("Invalid spec file path: path traversal detected")

    def get_local_version(self) -> Optional[str]:
        """Get version from local OpenAPI spec file.

        Returns:
            Version string from info.version field, or None if file doesn't exist
            or is malformed
        """
        if not self.spec_file.exists():
            return None

        try:
            file_size = self.spec_file.stat().st_size
            if file_size > self.MAX_SPEC_SIZE:
                return None

            with open(self.spec_file, "r", encoding="utf-8") as f:
                spec = json.load(f)

            version = spec.get("info", {}).get("version")
            return version if version else None

        except (json.JSONDecodeError, OSError, KeyError):
            return None

    def download_spec(self) -> Dict[str, Any]:
        """Download OpenAPI spec from public API.

        Returns:
            OpenAPI specification as dictionary

        Raises:
            SpecError: If response is not valid OpenAPI spec
        """
        try:
            response = requests.get(self.OPENAPI_URL, timeout=30, verify=True)
            response.raise_for_status()
            spec = response.json()

            if not isinstance(spec, dict):
                raise SpecError("Invalid response: expected JSON object")

            if "openapi" not in spec and "swagger" not in spec:
                raise SpecError("Invalid response: not an OpenAPI specification")

            if "info" not in spec:
                raise SpecError("Invalid response: missing 'info' field")

            return spec

        except requests.RequestException as e:
            raise SpecError(f"Failed to download OpenAPI spec: {type(e).__name__}") from e
        except (ValueError, KeyError) as e:
            raise SpecError(f"Invalid OpenAPI spec format: {type(e).__name__}") from e
        except SpecError:
            raise
        except Exception as e:
            raise SpecError(f"Unexpected error: {type(e).__name__}") from e

    def get_remote_version(self, spec_data: Dict[str, Any]) -> str:
        """Extract version from OpenAPI spec data.

        Args:
            spec_data: OpenAPI specification dictionary

        Returns:
            Version string from info.version field

        Raises:
            SpecError: If version field is missing
        """
        try:
            version = spec_data["info"]["version"]
            if not version:
                raise SpecError("Version field is empty")
            return version
        except KeyError as exc:
            raise SpecError("Missing 'info.version' field in OpenAPI spec") from exc

    def save_spec(self, spec_data: Dict[str, Any]) -> None:
        """Save OpenAPI spec to file atomically.

        Uses atomic write operation (temp file + rename) to prevent corruption.

        Args:
            spec_data: OpenAPI specification dictionary
        """
        if not isinstance(spec_data, dict):
            raise SpecError("Invalid spec data: must be a dictionary")

        self.data_dir.mkdir(parents=True, exist_ok=True)

        temp_file = self.spec_file.with_suffix(".tmp")

        try:
            spec_json = json.dumps(spec_data, indent=2, ensure_ascii=False)
            if len(spec_json) > self.MAX_SPEC_SIZE:
                raise SpecError("Spec file exceeds maximum allowed size")

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(spec_json)

            temp_file.replace(self.spec_file)

        except (OSError, TypeError, ValueError) as e:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise SpecError(f"Failed to save OpenAPI spec: {type(e).__name__}") from e
        except SpecError:
            raise
        except Exception as exc:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise SpecError("Failed to save OpenAPI spec: unexpected error") from exc

    def update_spec(self) -> Dict[str, Optional[str]]:
        """Update OpenAPI specification if version has changed.

        Downloads the remote spec, compares versions, and updates local
        file if the version is different.

        Returns:
            Dictionary with:
            - status: "first_download" | "updated" | "up_to_date"
            - local_version: Previous version (None if first download)
            - remote_version: Current version from API

        Raises:
            SpecError: If download or save fails
        """
        local_version = self.get_local_version()
        remote_spec = self.download_spec()
        remote_version = self.get_remote_version(remote_spec)

        if local_version is None:
            self.save_spec(remote_spec)
            return {
                "status": "first_download",
                "local_version": None,
                "remote_version": remote_version,
            }

        elif local_version != remote_version:
            self.save_spec(remote_spec)
            return {
                "status": "updated",
                "local_version": local_version,
                "remote_version": remote_version,
            }

        else:
            return {
                "status": "up_to_date",
                "local_version": local_version,
                "remote_version": remote_version,
            }
