"""Plugin system exceptions"""


class PluginError(Exception):
    """Base exception for plugin system"""
    pass


class PluginNotFoundError(PluginError):
    """Plugin not found"""
    pass


class PluginLoadError(PluginError):
    """Error loading plugin"""
    pass


class PluginConfigError(PluginError):
    """Plugin configuration error"""
    pass


class PluginDependencyError(PluginError):
    """Plugin dependency error"""
    pass


class PluginVersionError(PluginError):
    """Plugin version compatibility error"""
    pass


class PluginInitializationError(PluginError):
    """Plugin initialization error"""
    pass


class PluginExecutionError(PluginError):
    """Error during plugin execution"""
    pass