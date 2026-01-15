"""Tests for configuration system"""

import pytest
import tempfile
from pathlib import Path
import yaml

from docscope.core.config import Config, ScannerConfig, SearchConfig, StorageConfig


def test_default_config():
    """Test loading default configuration"""
    config = Config(config_file="nonexistent.yaml")
    
    assert config.version == "1.0"
    assert config.scanner.workers == 4
    assert config.search.engine == "whoosh"
    assert config.storage.backend == "sqlite"
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8080


def test_load_config_from_file():
    """Test loading configuration from YAML file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "version": "1.0",
            "scanner": {
                "workers": 8,
                "paths": [{"path": "/test/path"}],
            },
            "server": {
                "port": 9000,
            }
        }
        yaml.dump(config_data, f)
        config_file = f.name
    
    try:
        config = Config(config_file=config_file)
        assert config.scanner.workers == 8
        assert config.server.port == 9000
        assert config.scanner.paths[0]["path"] == "/test/path"
    finally:
        Path(config_file).unlink()


def test_config_get_method():
    """Test getting config values with dot notation"""
    config = Config()
    config.data = {
        "server": {
            "host": "localhost",
            "cors": {
                "enabled": True,
                "origins": ["*"]
            }
        }
    }
    
    assert config.get("server.host") == "localhost"
    assert config.get("server.cors.enabled") is True
    assert config.get("server.cors.origins") == ["*"]
    assert config.get("nonexistent.key", "default") == "default"


def test_scanner_config():
    """Test scanner configuration dataclass"""
    scanner = ScannerConfig(
        paths=[{"path": "/docs"}],
        ignore=["*.tmp"],
        workers=6
    )
    
    assert scanner.paths == [{"path": "/docs"}]
    assert scanner.ignore == ["*.tmp"]
    assert scanner.workers == 6


def test_ensure_directories(tmp_path):
    """Test that configuration creates required directories"""
    config_data = {
        "storage": {
            "sqlite": {
                "path": str(tmp_path / "test" / "docscope.db")
            }
        },
        "logging": {
            "file": str(tmp_path / "logs" / "docscope.log")
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name
    
    try:
        config = Config(config_file=config_file)
        
        # Check that directories were created
        assert (tmp_path / "test").exists()
        assert (tmp_path / "logs").exists()
    finally:
        Path(config_file).unlink()


def test_save_config(tmp_path):
    """Test saving configuration to file"""
    config = Config()
    config.data["test_key"] = "test_value"
    
    save_path = tmp_path / "test_config.yaml"
    config.save(str(save_path))
    
    assert save_path.exists()
    
    with open(save_path) as f:
        loaded = yaml.safe_load(f)
        assert loaded["test_key"] == "test_value"