"""Plugin registry for managing loaded plugins"""

from typing import Dict, List, Optional, Callable, Any
import logging

from .base import Plugin, PluginHook, PluginCapability
from .exceptions import PluginNotFoundError, PluginExecutionError

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for loaded plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[PluginHook, List[Callable]] = {}
        self.capabilities: Dict[PluginCapability, List[str]] = {}
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.api_routes: List[Dict[str, Any]] = []
        
    def register(self, plugin: Plugin) -> None:
        """Register a plugin"""
        metadata = plugin.get_metadata()
        name = metadata.name
        
        if name in self.plugins:
            logger.warning(f"Plugin '{name}' is already registered, replacing")
        
        self.plugins[name] = plugin
        
        # Register hooks
        for hook, handlers in plugin.get_hooks().items():
            if hook not in self.hooks:
                self.hooks[hook] = []
            self.hooks[hook].extend(handlers)
            logger.debug(f"Registered {len(handlers)} handlers for hook {hook} from plugin {name}")
        
        # Register capabilities
        for capability in metadata.capabilities:
            if capability not in self.capabilities:
                self.capabilities[capability] = []
            self.capabilities[capability].append(name)
            logger.debug(f"Registered capability {capability} for plugin {name}")
        
        # Register commands
        for cmd_name, cmd_info in plugin.get_commands().items():
            full_name = f"{name}:{cmd_name}"
            self.commands[full_name] = {
                'plugin': name,
                'handler': cmd_info['handler'],
                'description': cmd_info['description']
            }
            logger.debug(f"Registered command {full_name}")
        
        # Register API routes
        for route in plugin.get_api_routes():
            route['plugin'] = name
            self.api_routes.append(route)
            logger.debug(f"Registered API route {route['method']} {route['path']} from plugin {name}")
        
        logger.info(f"Successfully registered plugin: {name}")
    
    def unregister(self, name: str) -> None:
        """Unregister a plugin"""
        if name not in self.plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        
        plugin = self.plugins[name]
        metadata = plugin.get_metadata()
        
        # Remove hooks
        for hook, handlers in plugin.get_hooks().items():
            if hook in self.hooks:
                for handler in handlers:
                    if handler in self.hooks[hook]:
                        self.hooks[hook].remove(handler)
        
        # Remove capabilities
        for capability in metadata.capabilities:
            if capability in self.capabilities:
                if name in self.capabilities[capability]:
                    self.capabilities[capability].remove(name)
        
        # Remove commands
        commands_to_remove = [
            cmd for cmd in self.commands 
            if self.commands[cmd]['plugin'] == name
        ]
        for cmd in commands_to_remove:
            del self.commands[cmd]
        
        # Remove API routes
        self.api_routes = [
            route for route in self.api_routes 
            if route['plugin'] != name
        ]
        
        # Remove plugin
        del self.plugins[name]
        
        logger.info(f"Successfully unregistered plugin: {name}")
    
    def get_plugin(self, name: str) -> Plugin:
        """Get a plugin by name"""
        if name not in self.plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        return self.plugins[name]
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names"""
        return list(self.plugins.keys())
    
    def get_plugins_by_capability(self, capability: PluginCapability) -> List[Plugin]:
        """Get all plugins with a specific capability"""
        plugin_names = self.capabilities.get(capability, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def execute_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """Execute all handlers for a hook"""
        results = []
        handlers = self.hooks.get(hook, [])
        
        for handler in handlers:
            try:
                result = handler(*args, **kwargs)
                results.append(result)
                logger.debug(f"Executed hook {hook} handler successfully")
            except Exception as e:
                logger.error(f"Error executing hook {hook}: {e}")
                # Continue with other handlers
        
        return results
    
    async def execute_hook_async(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """Execute all handlers for a hook asynchronously"""
        import asyncio
        results = []
        handlers = self.hooks.get(hook, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(*args, **kwargs)
                else:
                    result = handler(*args, **kwargs)
                results.append(result)
                logger.debug(f"Executed async hook {hook} handler successfully")
            except Exception as e:
                logger.error(f"Error executing async hook {hook}: {e}")
                # Continue with other handlers
        
        return results
    
    def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute a plugin command"""
        if command not in self.commands:
            # Try without plugin prefix
            matching_commands = [
                cmd for cmd in self.commands 
                if cmd.split(':')[-1] == command
            ]
            if len(matching_commands) == 1:
                command = matching_commands[0]
            elif len(matching_commands) > 1:
                raise PluginExecutionError(
                    f"Ambiguous command '{command}'. "
                    f"Please specify plugin: {', '.join(matching_commands)}"
                )
            else:
                raise PluginNotFoundError(f"Command '{command}' not found")
        
        cmd_info = self.commands[command]
        plugin_name = cmd_info['plugin']
        plugin = self.get_plugin(plugin_name)
        
        if not plugin.enabled:
            raise PluginExecutionError(f"Plugin '{plugin_name}' is disabled")
        
        try:
            handler = cmd_info['handler']
            return handler(*args, **kwargs)
        except Exception as e:
            raise PluginExecutionError(f"Error executing command '{command}': {e}")
    
    def get_api_routes(self) -> List[Dict[str, Any]]:
        """Get all registered API routes"""
        # Only return routes from enabled plugins
        return [
            route for route in self.api_routes
            if route['plugin'] in self.plugins and self.plugins[route['plugin']].enabled
        ]
    
    def get_command_list(self) -> Dict[str, str]:
        """Get list of available commands with descriptions"""
        commands = {}
        for cmd_name, cmd_info in self.commands.items():
            plugin_name = cmd_info['plugin']
            if plugin_name in self.plugins and self.plugins[plugin_name].enabled:
                commands[cmd_name] = cmd_info['description']
        return commands
    
    def enable_plugin(self, name: str) -> None:
        """Enable a plugin"""
        plugin = self.get_plugin(name)
        plugin.on_enable()
        logger.info(f"Enabled plugin: {name}")
    
    def disable_plugin(self, name: str) -> None:
        """Disable a plugin"""
        plugin = self.get_plugin(name)
        plugin.on_disable()
        logger.info(f"Disabled plugin: {name}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get registry status"""
        return {
            'total_plugins': len(self.plugins),
            'enabled_plugins': sum(1 for p in self.plugins.values() if p.enabled),
            'total_hooks': sum(len(handlers) for handlers in self.hooks.values()),
            'total_commands': len(self.commands),
            'total_api_routes': len(self.api_routes),
            'capabilities': {
                cap.value: len(plugins) 
                for cap, plugins in self.capabilities.items()
            }
        }