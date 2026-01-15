"""Plugin manager for DocScope"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import threading

from .base import Plugin, PluginCapability, PluginHook
from .loader import PluginLoader
from .registry import PluginRegistry
from .exceptions import (
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginInitializationError
)
from ..core.config import Config

logger = logging.getLogger(__name__)


class PluginManager:
    """Manage plugin lifecycle and coordination"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config: Config = None):
        """Singleton pattern for plugin manager"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Config = None):
        """Initialize plugin manager"""
        if hasattr(self, '_initialized'):
            return
        
        self.config = config or Config()
        self.loader = PluginLoader(self.config)
        self.registry = PluginRegistry()
        self.initialized_plugins = set()
        self._plugin_state_file = Path.home() / ".docscope" / "plugin_state.json"
        self._load_state()
        self._initialized = True
    
    def discover(self) -> List[str]:
        """Discover available plugins"""
        return self.loader.discover_plugins()
    
    def load_plugin(self, name: str) -> Plugin:
        """Load and initialize a plugin"""
        if name in self.initialized_plugins:
            return self.registry.get_plugin(name)
        
        try:
            # Create plugin instance
            plugin = self.loader.create_plugin_instance(name)
            
            # Initialize plugin
            if not plugin.initialize():
                raise PluginInitializationError(f"Plugin '{name}' initialization failed")
            
            # Register plugin
            self.registry.register(plugin)
            self.initialized_plugins.add(name)
            
            # Execute startup hook
            self.registry.execute_hook(PluginHook.STARTUP)
            
            # Save state
            self._save_state()
            
            logger.info(f"Successfully loaded plugin: {name}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to load plugin '{name}': {e}")
            raise PluginLoadError(f"Failed to load plugin '{name}': {e}")
    
    def unload_plugin(self, name: str) -> None:
        """Unload a plugin"""
        if name not in self.initialized_plugins:
            raise PluginNotFoundError(f"Plugin '{name}' is not loaded")
        
        try:
            # Get plugin
            plugin = self.registry.get_plugin(name)
            
            # Execute shutdown hook
            self.registry.execute_hook(PluginHook.SHUTDOWN)
            
            # Shutdown plugin
            plugin.shutdown()
            
            # Unregister plugin
            self.registry.unregister(name)
            self.initialized_plugins.remove(name)
            
            # Save state
            self._save_state()
            
            logger.info(f"Successfully unloaded plugin: {name}")
            
        except Exception as e:
            logger.error(f"Failed to unload plugin '{name}': {e}")
            raise PluginError(f"Failed to unload plugin '{name}': {e}")
    
    def reload_plugin(self, name: str) -> Plugin:
        """Reload a plugin"""
        # Unload if loaded
        if name in self.initialized_plugins:
            self.unload_plugin(name)
        
        # Load again
        return self.load_plugin(name)
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        try:
            # Load if not loaded
            if name not in self.initialized_plugins:
                self.load_plugin(name)
            
            # Enable
            self.registry.enable_plugin(name)
            
            # Save state
            self._save_state()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable plugin '{name}': {e}")
            return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        try:
            if name not in self.initialized_plugins:
                raise PluginNotFoundError(f"Plugin '{name}' is not loaded")
            
            # Disable
            self.registry.disable_plugin(name)
            
            # Save state
            self._save_state()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable plugin '{name}': {e}")
            return False
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins with their status"""
        plugins = []
        
        # Get all discovered plugins
        discovered = self.discover()
        
        for name in discovered:
            plugin_info = {
                'name': name,
                'loaded': name in self.initialized_plugins,
                'enabled': False,
                'version': None,
                'author': None,
                'description': None
            }
            
            # Get additional info if loaded
            if name in self.initialized_plugins:
                try:
                    plugin = self.registry.get_plugin(name)
                    metadata = plugin.get_metadata()
                    plugin_info.update({
                        'enabled': plugin.enabled,
                        'version': metadata.version,
                        'author': metadata.author,
                        'description': metadata.description,
                        'capabilities': [c.value for c in metadata.capabilities]
                    })
                except Exception as e:
                    logger.warning(f"Failed to get info for plugin '{name}': {e}")
            
            plugins.append(plugin_info)
        
        return plugins
    
    def get_plugin_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a plugin"""
        if name not in self.discover():
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        
        info = {
            'name': name,
            'available': True,
            'loaded': name in self.initialized_plugins
        }
        
        # Try to get metadata without loading
        try:
            plugin_class = self.loader.load_plugin(name)
            temp_instance = plugin_class({})
            metadata = temp_instance.get_metadata()
            
            info.update({
                'version': metadata.version,
                'author': metadata.author,
                'description': metadata.description,
                'website': metadata.website,
                'license': metadata.license,
                'dependencies': metadata.dependencies,
                'capabilities': [c.value for c in metadata.capabilities],
                'hooks': [h.value for h in metadata.hooks],
                'config_schema': metadata.config_schema,
                'tags': metadata.tags,
                'min_docscope_version': metadata.min_docscope_version,
                'max_docscope_version': metadata.max_docscope_version
            })
            
            # Add runtime info if loaded
            if name in self.initialized_plugins:
                plugin = self.registry.get_plugin(name)
                info['enabled'] = plugin.enabled
                info['status'] = plugin.get_status()
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def install_plugin(self, name: str, version: str = None) -> Dict[str, Any]:
        """Install a plugin from repository (placeholder)"""
        # This would connect to a plugin repository
        # For now, just return a placeholder
        return {
            'name': name,
            'version': version or 'latest',
            'status': 'not_implemented'
        }
    
    def uninstall_plugin(self, name: str, keep_config: bool = False) -> bool:
        """Uninstall a plugin"""
        # Unload if loaded
        if name in self.initialized_plugins:
            self.unload_plugin(name)
        
        # Remove plugin files (placeholder)
        # This would remove the plugin directory
        
        return True
    
    def install_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Install a plugin from a file"""
        # This would extract and install a plugin package
        # For now, just return a placeholder
        return {
            'file': str(file_path),
            'status': 'not_implemented'
        }
    
    def search_plugins(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for plugins in repository (placeholder)"""
        # This would search a plugin repository
        # For now, return local plugins matching query
        results = []
        
        for plugin_info in self.list_plugins():
            name = plugin_info['name']
            description = plugin_info.get('description', '')
            
            if query.lower() in name.lower() or query.lower() in description.lower():
                results.append(plugin_info)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def execute_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """Execute a hook through the registry"""
        return self.registry.execute_hook(hook, *args, **kwargs)
    
    async def execute_hook_async(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """Execute a hook asynchronously through the registry"""
        return await self.registry.execute_hook_async(hook, *args, **kwargs)
    
    def get_plugins_by_capability(self, capability: PluginCapability) -> List[Plugin]:
        """Get all plugins with a specific capability"""
        return self.registry.get_plugins_by_capability(capability)
    
    def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute a plugin command"""
        return self.registry.execute_command(command, *args, **kwargs)
    
    def get_api_routes(self) -> List[Dict[str, Any]]:
        """Get all plugin API routes"""
        return self.registry.get_api_routes()
    
    def _load_state(self) -> None:
        """Load plugin state from file"""
        if not self._plugin_state_file.exists():
            return
        
        try:
            with open(self._plugin_state_file) as f:
                state = json.load(f)
            
            # Auto-load previously enabled plugins
            if self.config.plugins and hasattr(self.config.plugins, 'autoload'):
                if self.config.plugins.autoload:
                    for plugin_name in state.get('enabled', []):
                        try:
                            self.load_plugin(plugin_name)
                            logger.info(f"Auto-loaded plugin: {plugin_name}")
                        except Exception as e:
                            logger.warning(f"Failed to auto-load plugin '{plugin_name}': {e}")
            
        except Exception as e:
            logger.warning(f"Failed to load plugin state: {e}")
    
    def _save_state(self) -> None:
        """Save plugin state to file"""
        try:
            # Create directory if needed
            self._plugin_state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Get enabled plugins
            enabled = [
                name for name in self.initialized_plugins
                if self.registry.get_plugin(name).enabled
            ]
            
            state = {
                'enabled': enabled,
                'loaded': list(self.initialized_plugins)
            }
            
            with open(self._plugin_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
        except Exception as e:
            logger.warning(f"Failed to save plugin state: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin manager status"""
        return {
            'discovered': len(self.discover()),
            'loaded': len(self.initialized_plugins),
            'registry': self.registry.get_status(),
            'plugin_directories': [str(d) for d in self.loader.plugin_dirs]
        }


# Global instance getter
def get_plugin_manager(config: Config = None) -> PluginManager:
    """Get the global plugin manager instance"""
    return PluginManager(config)