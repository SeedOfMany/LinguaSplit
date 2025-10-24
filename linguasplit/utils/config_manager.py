"""
Configuration management for LinguaSplit.
Handles settings persistence using JSON storage.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class ConfigManager:
    """
    Manages application settings with JSON persistence.

    Features:
    - Load/save settings to JSON file
    - Default configuration values
    - Handle missing config gracefully
    - Type-safe config access
    """

    DEFAULT_CONFIG = {
        # Output settings
        'output': {
            'format': 'markdown',  # markdown, text, json
            'include_metadata': True,
            'include_page_markers': True,
            'preserve_formatting': True,
        },

        # Language detection
        'language': {
            'auto_detect': True,
            'default_language': 'english',
            'min_confidence': 0.5,
        },

        # Layout detection
        'layout': {
            'detect_columns': True,
            'min_column_width': 100,
            'column_gap_threshold': 50,
            'detect_tables': False,
        },

        # Text processing
        'processing': {
            'clean_text': True,
            'remove_headers_footers': True,
            'normalize_whitespace': True,
            'fix_hyphenation': True,
        },

        # OCR settings
        'ocr': {
            'enabled': False,
            'engine': 'tesseract',  # tesseract, easyocr
            'language': 'eng',
            'dpi': 300,
        },

        # Batch processing
        'batch': {
            'max_workers': 4,
            'continue_on_error': True,
            'create_summary': True,
        },

        # GUI settings
        'gui': {
            'theme': 'system',  # system, light, dark
            'window_size': [1000, 700],
            'show_preview': True,
            'auto_save_settings': True,
        },

        # Logging
        'logging': {
            'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
            'log_to_file': False,
            'log_file': 'linguasplit.log',
        },

        # Application info
        'app': {
            'version': '1.0.0',
            'last_updated': None,
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config file (default: ~/.linguasplit/config.json)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Use user's home directory
            config_dir = Path.home() / '.linguasplit'
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / 'config.json'

        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        # Start with default config
        config = self.DEFAULT_CONFIG.copy()

        # Try to load from file
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)

                # Merge user config with defaults
                config = self._merge_configs(config, user_config)

            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration.")

        return config

    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """
        Recursively merge user config with default config.

        Args:
            default: Default configuration
            user: User configuration

        Returns:
            Merged configuration
        """
        result = default.copy()

        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = self._merge_configs(result[key], value)
            else:
                # Use user value
                result[key] = value

        return result

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update last_updated timestamp
            self.config['app']['last_updated'] = datetime.now().isoformat()

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write config file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error: Failed to save config to {self.config_path}: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Path to value (e.g., 'output.format')
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any, save: bool = True) -> bool:
        """
        Set configuration value using dot notation.

        Args:
            key_path: Path to value (e.g., 'output.format')
            value: Value to set
            save: Whether to save to file immediately

        Returns:
            True if successful
        """
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

        # Save if requested
        if save:
            return self.save()

        return True

    def reset(self, save: bool = True) -> bool:
        """
        Reset configuration to defaults.

        Args:
            save: Whether to save to file immediately

        Returns:
            True if successful
        """
        self.config = self.DEFAULT_CONFIG.copy()

        if save:
            return self.save()

        return True

    def get_all(self) -> Dict:
        """
        Get entire configuration.

        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()

    def update(self, updates: Dict, save: bool = True) -> bool:
        """
        Update multiple configuration values.

        Args:
            updates: Dictionary of updates
            save: Whether to save to file immediately

        Returns:
            True if successful
        """
        self.config = self._merge_configs(self.config, updates)

        if save:
            return self.save()

        return True

    def export_config(self, path: str) -> bool:
        """
        Export configuration to a specific file.

        Args:
            path: Export file path

        Returns:
            True if successful
        """
        try:
            export_path = Path(path)
            export_path.parent.mkdir(parents=True, exist_ok=True)

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error: Failed to export config to {path}: {e}")
            return False

    def import_config(self, path: str, save: bool = True) -> bool:
        """
        Import configuration from a file.

        Args:
            path: Import file path
            save: Whether to save imported config

        Returns:
            True if successful
        """
        try:
            import_path = Path(path)

            if not import_path.exists():
                print(f"Error: Config file not found: {path}")
                return False

            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            # Merge with defaults to ensure all keys exist
            self.config = self._merge_configs(self.DEFAULT_CONFIG, imported_config)

            if save:
                return self.save()

            return True

        except Exception as e:
            print(f"Error: Failed to import config from {path}: {e}")
            return False

    def has_key(self, key_path: str) -> bool:
        """
        Check if configuration key exists.

        Args:
            key_path: Path to check (e.g., 'output.format')

        Returns:
            True if key exists
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return False

        return True

    def delete_key(self, key_path: str, save: bool = True) -> bool:
        """
        Delete a configuration key.

        Args:
            key_path: Path to key to delete
            save: Whether to save after deletion

        Returns:
            True if successful
        """
        keys = key_path.split('.')
        config = self.config

        # Navigate to parent
        for key in keys[:-1]:
            if key not in config:
                return False
            config = config[key]

        # Delete the key
        if keys[-1] in config:
            del config[keys[-1]]

            if save:
                return self.save()

            return True

        return False

    def get_config_path(self) -> str:
        """
        Get configuration file path.

        Returns:
            Path to config file
        """
        return str(self.config_path)
