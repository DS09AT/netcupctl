"""Configuration management for netcupctl."""

import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages configuration directory and files."""

    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = self._get_config_dir()
        self.tokens_file = self.config_dir / "tokens.json"
        self.config_file = self.config_dir / "config.json"

    def _get_config_dir(self) -> Path:
        """Determine configuration directory based on platform.

        Returns:
            Path to configuration directory:
            - Linux/macOS: ~/.config/netcupctl
            - Windows: %APPDATA%/netcupctl
        """
        system = platform.system()

        if system == "Windows":
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / "netcupctl"
            return Path.home() / "AppData" / "Roaming" / "netcupctl"
        else:
            xdg_config_home = os.getenv("XDG_CONFIG_HOME")
            if xdg_config_home:
                return Path(xdg_config_home) / "netcupctl"
            return Path.home() / ".config" / "netcupctl"

    def ensure_config_dir(self) -> None:
        """Create configuration directory if it doesn't exist.

        Sets directory permissions to 700 (owner read/write/execute only).
        """
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, mode=0o700)
        else:
            try:
                os.chmod(self.config_dir, 0o700)
            except (OSError, NotImplementedError):
                pass

    def load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON from file.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary with JSON data or None if file doesn't exist
        """
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def save_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save data as JSON to file.

        Args:
            file_path: Path to JSON file
            data: Dictionary to save as JSON
        """
        self.ensure_config_dir()

        temp_file = file_path.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        try:
            os.chmod(temp_file, 0o600)
        except (OSError, NotImplementedError):
            pass

        temp_file.replace(file_path)

    def delete_file(self, file_path: Path) -> bool:
        """Delete a file.

        Args:
            file_path: Path to file to delete

        Returns:
            True if file was deleted, False if it didn't exist
        """
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def load_tokens(self) -> Optional[Dict[str, Any]]:
        """Load tokens from tokens.json.

        Validates that required fields exist. Automatically deletes
        corrupted or invalid token files.

        Returns:
            Dictionary with token data or None if not found/invalid
        """
        tokens = self.load_json(self.tokens_file)
        if tokens is None:
            return None

        required_fields = ("access_token", "refresh_token", "expires_at")
        if not all(field in tokens and tokens[field] for field in required_fields):
            self.delete_tokens()
            return None

        return tokens

    def save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Save tokens to tokens.json.

        Args:
            tokens: Dictionary with token data
        """
        self.save_json(self.tokens_file, tokens)

    def delete_tokens(self) -> bool:
        """Delete tokens.json file.

        Returns:
            True if file was deleted, False if it didn't exist
        """
        return self.delete_file(self.tokens_file)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json.

        Returns:
            Dictionary with configuration or empty dict if not found
        """
        return self.load_json(self.config_file) or {}

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to config.json.

        Args:
            config: Dictionary with configuration
        """
        self.save_json(self.config_file, config)
