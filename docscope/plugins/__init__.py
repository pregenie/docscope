"""DocScope Plugin System"""

from .base import Plugin, PluginMetadata, PluginCapability, PluginHook
from .manager import PluginManager
from .loader import PluginLoader
from .registry import PluginRegistry
from .exceptions import (
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginConfigError,
    PluginDependencyError
)

__all__ = [
    'Plugin',
    'PluginMetadata',
    'PluginCapability',
    'PluginHook',
    'PluginManager',
    'PluginLoader',
    'PluginRegistry',
    'PluginError',
    'PluginNotFoundError',
    'PluginLoadError',
    'PluginConfigError',
    'PluginDependencyError'
]