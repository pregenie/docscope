"""Configuration management for DocScope"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dataclasses import dataclass, field


@dataclass
class ScannerConfig:
    """Scanner configuration"""
    paths: List[Dict[str, Any]] = field(default_factory=list)
    ignore: List[str] = field(default_factory=list)
    formats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    workers: int = 4
    
    
@dataclass
class SearchConfig:
    """Search engine configuration"""
    engine: str = "whoosh"
    settings: Dict[str, Any] = field(default_factory=dict)
    scoring: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageConfig:
    """Storage configuration"""
    backend: str = "sqlite"
    sqlite: Dict[str, Any] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 4
    reload: bool = False
    cors: Dict[str, Any] = field(default_factory=dict)
    auth: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    console: bool = True


class Config:
    """Main configuration class for DocScope"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from file or defaults"""
        self.config_file = config_file or self._find_config_file()
        self.data = self._load_config()
        
        # Parse configuration sections
        self.scanner = self._parse_scanner_config()
        self.search = self._parse_search_config()
        self.storage = self._parse_storage_config()
        self.server = self._parse_server_config()
        self.logging = self._parse_logging_config()
        
        # Additional settings
        self.version = self.data.get("version", "1.0")
        self.plugins = self.data.get("plugins", {})
        self.monitoring = self.data.get("monitoring", {})
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _find_config_file(self) -> str:
        """Find configuration file in common locations"""
        search_paths = [
            Path.cwd() / ".docscope.yaml",
            Path.cwd() / "docscope.yaml",
            Path.home() / ".docscope" / "config.yaml",
            Path.home() / ".config" / "docscope" / "config.yaml",
        ]
        
        for path in search_paths:
            if path.exists():
                return str(path)
        
        # Return default path if no config found
        return str(Path.cwd() / ".docscope.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_file or not Path(self.config_file).exists():
            return self._get_defaults()
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_file}: {e}")
            return self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "version": "1.0",
            "scanner": {
                "paths": [{"path": "./docs", "recursive": True}],
                "ignore": ["**/__pycache__", "**/.git", "**/node_modules"],
                "formats": {
                    "markdown": {"enabled": True, "extensions": [".md"]},
                    "text": {"enabled": True, "extensions": [".txt"]},
                }
            },
            "search": {
                "engine": "whoosh",
                "settings": {
                    "fuzzy": True,
                    "max_results": 100,
                    "highlight": True,
                }
            },
            "storage": {
                "backend": "sqlite",
                "sqlite": {"path": "~/.docscope/docscope.db"}
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "workers": 4,
            },
            "logging": {
                "level": "INFO",
                "console": True,
            }
        }
    
    def _parse_scanner_config(self) -> ScannerConfig:
        """Parse scanner configuration"""
        scanner_data = self.data.get("scanner", {})
        return ScannerConfig(
            paths=scanner_data.get("paths", []),
            ignore=scanner_data.get("ignore", []),
            formats=scanner_data.get("formats", {}),
            workers=scanner_data.get("workers", 4),
        )
    
    def _parse_search_config(self) -> SearchConfig:
        """Parse search configuration"""
        search_data = self.data.get("search", {})
        return SearchConfig(
            engine=search_data.get("engine", "whoosh"),
            settings=search_data.get("settings", {}),
            scoring=search_data.get("scoring", {}),
        )
    
    def _parse_storage_config(self) -> StorageConfig:
        """Parse storage configuration"""
        storage_data = self.data.get("storage", {})
        return StorageConfig(
            backend=storage_data.get("backend", "sqlite"),
            sqlite=storage_data.get("sqlite", {}),
            cache=storage_data.get("cache", {}),
        )
    
    def _parse_server_config(self) -> ServerConfig:
        """Parse server configuration"""
        server_data = self.data.get("server", {})
        return ServerConfig(
            host=server_data.get("host", "0.0.0.0"),
            port=server_data.get("port", 8080),
            workers=server_data.get("workers", 4),
            reload=server_data.get("reload", False),
            cors=server_data.get("cors", {}),
            auth=server_data.get("auth", {}),
            rate_limit=server_data.get("rate_limit", {}),
        )
    
    def _parse_logging_config(self) -> LoggingConfig:
        """Parse logging configuration"""
        logging_data = self.data.get("logging", {})
        return LoggingConfig(
            level=logging_data.get("level", "INFO"),
            format=logging_data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file=logging_data.get("file"),
            console=logging_data.get("console", True),
        )
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        # Expand home directory in paths
        if self.storage.sqlite.get("path"):
            db_path = Path(os.path.expanduser(self.storage.sqlite["path"]))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.logging.file:
            log_path = Path(os.path.expanduser(self.logging.file))
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create docscope home directory
        docscope_home = Path.home() / ".docscope"
        docscope_home.mkdir(exist_ok=True)
        
        # Create plugins directory if enabled
        if self.plugins.get("enabled"):
            plugin_dir = Path(os.path.expanduser(
                self.plugins.get("directory", "~/.docscope/plugins")
            ))
            plugin_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, path: Optional[str] = None):
        """Save configuration to file"""
        save_path = path or self.config_file
        with open(save_path, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value