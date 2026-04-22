"""
BudConfig - Configuration management for budtestlibrary.

Loads configuration from:
1. Environment variables (highest priority)
2. app.properties file
3. Default values

Environment variables:
    BUD_BACKEND_URL - Backend API URL (default: https://bud.embedlabs.de/)
    BUD_FRONTEND_URL - Frontend URL (default: https://bud.embedlabs.de/)
    BUD_TOKEN - Authentication token for the backend
    BLOOM_URL - Bloom PLM URL (default: https://bloom.embedlabs.de/)
    BLOOM_TOKEN - Bloom PLM JWT token
    BLOOM_EMAIL - Bloom PLM login email
    BLOOM_PASSWORD - Bloom PLM login password
    BUD_RUNNER_ACCOUNT - Runner account name
    BUD_RUNNER_TOKEN - Runner authentication token
    BUD_RUNNER_SOCKET_PORT - Socket port for runner communication
"""

import os
import configparser
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class BudConfig:
    """
    Configuration container for budtestlibrary.
    
    Automatically loads from environment variables and app.properties.
    Environment variables take precedence over file configuration.
    
    Usage:
        config = BudConfig()
        print(config.backend_url)
        print(config.bloom_url)
        
        # With custom properties file
        config = BudConfig(properties_file="/path/to/app.properties")
    """
    
    # Backend configuration
    backend_url: str = ""
    frontend_url: str = ""
    bud_token: Optional[str] = None
    
    # Bloom PLM configuration
    bloom_url: str = ""
    bloom_token: Optional[str] = None
    bloom_email: Optional[str] = None
    bloom_password: Optional[str] = None
    
    # Runner configuration
    runner_account: Optional[str] = None
    runner_token: Optional[str] = None
    runner_socket_port: int = 53035
    runner_timeout: int = -1  # -1 = unlimited
    
    # GitHub/GitLab configuration
    config_project_api_url: Optional[str] = None
    config_project_repo: Optional[str] = None
    config_token: Optional[str] = None
    config_branch: str = "main"
    config_file: str = "bud_config.json"
    config_folder: str = "git-config"
    
    # User configuration
    last_user: Optional[str] = None
    location: str = "EmbedLabs - Test Environment"
    language: str = "en"
    
    # UI configuration
    full_screen: bool = False
    test_image_height: float = 500.0
    
    # Internal
    _properties_file: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        """Load configuration from files and environment."""
        if self._properties_file:
            self._load_from_properties(self._properties_file)
        else:
            # Try to find app.properties in current directory or parent
            for path in [Path("app.properties"), Path("../app.properties")]:
                if path.exists():
                    self._load_from_properties(str(path))
                    break
        
        # Environment variables override file settings
        self._load_from_env()

    def _load_from_properties(self, filepath: str) -> None:
        """
        Load configuration from a .properties file.
        
        Uses configparser with a fake section header for Java-style properties.
        """
        try:
            # Create a fake section for configparser
            with open(filepath, "r") as f:
                content = "[DEFAULT]\n" + f.read()
            
            config = configparser.ConfigParser()
            config.read_string(content)
            
            props = config["DEFAULT"]
            
            # Map properties to config attributes
            property_mapping = {
                "budBackend": ("backend_url", str),
                "budFrontend": ("frontend_url", str),
                "budToken": ("bud_token", str),
                "bloomUrl": ("bloom_url", str),
                "bloomToken": ("bloom_token", str),
                "bloomEmail": ("bloom_email", str),
                "bloomPassword": ("bloom_password", str),
                "budRunnerAccount": ("runner_account", str),
                "budRunnerToken": ("runner_token", str),
                "runnerSocketPort": ("runner_socket_port", int),
                "runnerTimeout": ("runner_timeout", int),
                "configProjectApiUrl": ("config_project_api_url", str),
                "configProjectRepo": ("config_project_repo", str),
                "configToken": ("config_token", str),
                "configBranch": ("config_branch", str),
                "configFile": ("config_file", str),
                "configFolder": ("config_folder", str),
                "lastUser": ("last_user", str),
                "location": ("location", str),
                "language": ("language", str),
                "fullScreen": ("full_screen", lambda x: x.lower() == "true"),
                "testImageHeight": ("test_image_height", float),
            }
            
            for prop_key, (attr_name, converter) in property_mapping.items():
                if prop_key in props:
                    try:
                        setattr(self, attr_name, converter(props[prop_key]))
                    except (ValueError, TypeError):
                        pass  # Keep default if conversion fails
                        
        except FileNotFoundError:
            pass  # Use defaults if file not found
        except Exception as e:
            print(f"Warning: Error loading properties file: {e}")

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "BUD_BACKEND_URL": ("backend_url", str),
            "BUD_FRONTEND_URL": ("frontend_url", str),
            "BUD_TOKEN": ("bud_token", str),
            "BLOOM_URL": ("bloom_url", str),
            "BLOOM_TOKEN": ("bloom_token", str),
            "BLOOM_EMAIL": ("bloom_email", str),
            "BLOOM_PASSWORD": ("bloom_password", str),
            "BUD_RUNNER_ACCOUNT": ("runner_account", str),
            "BUD_RUNNER_TOKEN": ("runner_token", str),
            "BUD_RUNNER_SOCKET_PORT": ("runner_socket_port", int),
            "BUD_RUNNER_TIMEOUT": ("runner_timeout", int),
            "BUD_CONFIG_PROJECT_API_URL": ("config_project_api_url", str),
            "BUD_CONFIG_PROJECT_REPO": ("config_project_repo", str),
            "BUD_CONFIG_TOKEN": ("config_token", str),
            "BUD_CONFIG_BRANCH": ("config_branch", str),
            "BUD_CONFIG_FILE": ("config_file", str),
            "BUD_LOCATION": ("location", str),
        }
        
        for env_key, (attr_name, converter) in env_mapping.items():
            value = os.environ.get(env_key)
            if value is not None:
                try:
                    setattr(self, attr_name, converter(value))
                except (ValueError, TypeError):
                    pass  # Keep existing value if conversion fails

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive tokens)."""
        return {
            "backend_url": self.backend_url,
            "frontend_url": self.frontend_url,
            "bloom_url": self.bloom_url,
            "runner_account": self.runner_account,
            "runner_socket_port": self.runner_socket_port,
            "runner_timeout": self.runner_timeout,
            "config_branch": self.config_branch,
            "config_file": self.config_file,
            "location": self.location,
            "language": self.language,
            "full_screen": self.full_screen,
        }

    def ensure_trailing_slash(self, url: str) -> str:
        """Ensure URL has trailing slash."""
        return url if url.endswith("/") else f"{url}/"

    @property
    def api_base_url(self) -> str:
        """Get the API base URL."""
        return self.ensure_trailing_slash(self.backend_url) + "api/"

    @property
    def upload_url(self) -> str:
        """Get the file upload URL."""
        return self.api_base_url + "uploads"

    @property
    def test_runs_url(self) -> str:
        """Get the test runs API URL."""
        return self.api_base_url + "test-runs"

    @property
    def runners_url(self) -> str:
        """Get the runners API URL."""
        return self.api_base_url + "runners"


# Default configuration instance
default_config = BudConfig()
