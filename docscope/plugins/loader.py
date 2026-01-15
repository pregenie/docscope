"""Plugin loader for DocScope"""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
import logging

from .base import Plugin, PluginMetadata
from .exceptions import (
    PluginLoadError,
    PluginConfigError,
    PluginVersionError,
    PluginDependencyError
)
from ..core.config import Config

logger = logging.getLogger(__name__)


class PluginLoader:
    """Load and validate plugins"""
    
    def __init__(self, config: Config):
        self.config = config
        self.plugin_dirs = self._get_plugin_directories()
        self.loaded_modules = {}
        
    def _get_plugin_directories(self) -> List[Path]:
        """Get plugin directories from configuration"""
        dirs = []
        
        # Default plugin directories
        default_dirs = [
            Path.home() / ".docscope" / "plugins",
            Path.cwd() / "plugins",
            Path(__file__).parent / "builtin"
        ]
        
        # Add configured directories
        if hasattr(self.config, 'plugins') and self.config.plugins:
            if hasattr(self.config.plugins, 'directories'):
                for dir_path in self.config.plugins.directories:
                    dirs.append(Path(dir_path))
        
        # Add default directories
        for dir_path in default_dirs:
            if dir_path not in dirs:
                dirs.append(dir_path)
        
        # Filter existing directories
        existing_dirs = [d for d in dirs if d.exists() and d.is_dir()]
        
        return existing_dirs
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            # Look for plugin packages (directories with __init__.py)
            for item in plugin_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    plugin_name = item.name
                    if plugin_name not in discovered:
                        discovered.append(plugin_name)
                        logger.debug(f"Discovered plugin: {plugin_name} in {plugin_dir}")
                
                # Also look for single-file plugins
                elif item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                    plugin_name = item.stem
                    if plugin_name not in discovered:
                        discovered.append(plugin_name)
                        logger.debug(f"Discovered plugin: {plugin_name} in {plugin_dir}")
        
        return discovered
    
    def load_plugin(self, name: str) -> Type[Plugin]:
        """Load a plugin class by name"""
        if name in self.loaded_modules:
            return self.loaded_modules[name]
        
        plugin_class = None
        
        # Try to load from each plugin directory
        for plugin_dir in self.plugin_dirs:
            # Try package format
            package_path = plugin_dir / name
            if package_path.is_dir() and (package_path / "__init__.py").exists():
                try:
                    plugin_class = self._load_package_plugin(name, package_path)
                    if plugin_class:
                        break
                except Exception as e:
                    logger.warning(f"Failed to load plugin package {name} from {package_path}: {e}")
            
            # Try single file format
            file_path = plugin_dir / f"{name}.py"
            if file_path.is_file():
                try:
                    plugin_class = self._load_file_plugin(name, file_path)
                    if plugin_class:
                        break
                except Exception as e:
                    logger.warning(f"Failed to load plugin file {name} from {file_path}: {e}")
        
        if not plugin_class:
            raise PluginLoadError(f"Plugin '{name}' not found in any plugin directory")
        
        # Validate plugin class
        if not issubclass(plugin_class, Plugin):
            raise PluginLoadError(f"Plugin '{name}' does not inherit from Plugin base class")
        
        self.loaded_modules[name] = plugin_class
        return plugin_class
    
    def _load_package_plugin(self, name: str, path: Path) -> Optional[Type[Plugin]]:
        """Load a plugin from a package"""
        # Check for plugin.json metadata
        metadata_file = path / "plugin.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                logger.debug(f"Loaded metadata for plugin {name}: {metadata}")
        
        # Add plugin directory to path temporarily
        sys.path.insert(0, str(path.parent))
        
        try:
            # Import the module
            module = importlib.import_module(name)
            
            # Find the Plugin subclass
            plugin_class = self._find_plugin_class(module)
            
            return plugin_class
            
        finally:
            # Remove from path
            sys.path.remove(str(path.parent))
    
    def _load_file_plugin(self, name: str, path: Path) -> Optional[Type[Plugin]]:
        """Load a plugin from a single file"""
        # Load the module from file
        spec = importlib.util.spec_from_file_location(name, path)
        if not spec or not spec.loader:
            raise PluginLoadError(f"Cannot load plugin spec from {path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        
        # Find the Plugin subclass
        plugin_class = self._find_plugin_class(module)
        
        return plugin_class
    
    def _find_plugin_class(self, module) -> Optional[Type[Plugin]]:
        """Find the Plugin subclass in a module"""
        from .base import Plugin
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Plugin) and 
                attr != Plugin and
                not attr.__name__.startswith('_')):
                return attr
        
        return None
    
    def load_plugin_config(self, name: str) -> Dict:
        """Load configuration for a plugin"""
        config = {}
        
        # Check for plugin-specific config file
        for plugin_dir in self.plugin_dirs:
            config_file = plugin_dir / name / "config.json"
            if config_file.exists():
                with open(config_file) as f:
                    config.update(json.load(f))
                break
        
        # Override with user configuration
        if hasattr(self.config, 'plugins') and self.config.plugins:
            if hasattr(self.config.plugins, 'configs'):
                plugin_configs = self.config.plugins.configs
                if name in plugin_configs:
                    config.update(plugin_configs[name])
        
        return config
    
    def validate_plugin(self, plugin_class: Type[Plugin]) -> bool:
        """Validate a plugin before instantiation"""
        try:
            # Create temporary instance to get metadata
            temp_instance = plugin_class({})
            metadata = temp_instance.get_metadata()
            
            # Check version compatibility
            if metadata.min_docscope_version:
                from .. import __version__
                if not self._check_version(__version__, metadata.min_docscope_version, '>='):
                    raise PluginVersionError(
                        f"Plugin requires DocScope >= {metadata.min_docscope_version}, "
                        f"current version is {__version__}"
                    )
            
            if metadata.max_docscope_version:
                from .. import __version__
                if not self._check_version(__version__, metadata.max_docscope_version, '<='):
                    raise PluginVersionError(
                        f"Plugin requires DocScope <= {metadata.max_docscope_version}, "
                        f"current version is {__version__}"
                    )
            
            # Check dependencies
            for dep in metadata.dependencies:
                if not self._check_dependency(dep):
                    raise PluginDependencyError(f"Plugin dependency not satisfied: {dep}")
            
            return True
            
        except Exception as e:
            logger.error(f"Plugin validation failed: {e}")
            return False
    
    def _check_version(self, current: str, required: str, operator: str) -> bool:
        """Check version compatibility"""
        from packaging import version
        
        current_v = version.parse(current)
        required_v = version.parse(required)
        
        if operator == '>=':
            return current_v >= required_v
        elif operator == '<=':
            return current_v <= required_v
        elif operator == '==':
            return current_v == required_v
        else:
            return False
    
    def _check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is satisfied"""
        # Check Python package dependencies
        if dependency.startswith('pip:'):
            package = dependency[4:]
            try:
                importlib.import_module(package.split('>=')[0].split('==')[0])
                return True
            except ImportError:
                return False
        
        # Check other plugins
        elif dependency.startswith('plugin:'):
            plugin_name = dependency[7:]
            return plugin_name in self.discover_plugins()
        
        # Check system commands
        elif dependency.startswith('cmd:'):
            command = dependency[4:]
            import shutil
            return shutil.which(command) is not None
        
        return True
    
    def create_plugin_instance(self, name: str) -> Plugin:
        """Create an instance of a plugin"""
        # Load the plugin class
        plugin_class = self.load_plugin(name)
        
        # Validate the plugin
        if not self.validate_plugin(plugin_class):
            raise PluginLoadError(f"Plugin '{name}' validation failed")
        
        # Load configuration
        config = self.load_plugin_config(name)
        
        # Create instance
        try:
            plugin = plugin_class(config)
            
            # Validate configuration
            if not plugin.validate_config():
                raise PluginConfigError(f"Plugin '{name}' configuration validation failed")
            
            return plugin
            
        except Exception as e:
            raise PluginLoadError(f"Failed to create plugin instance: {e}")
    
    def load_plugin_from_file(self, file_path: Path) -> Type[Plugin]:
        """Load a plugin from a specific file path"""
        return self._load_file_plugin(file_path.stem, file_path)
    
    def check_dependencies(self, metadata: PluginMetadata) -> bool:
        """Check if all plugin dependencies are satisfied"""
        for dep in metadata.dependencies:
            if not self._check_dependency(dep):
                logger.error(f"Missing dependency: {dep}")
                return False
        return True