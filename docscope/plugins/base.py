"""Plugin base classes and interfaces"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging


class PluginCapability(Enum):
    """Plugin capabilities"""
    SCANNER = "scanner"          # Can scan documents
    PROCESSOR = "processor"      # Can process documents
    STORAGE = "storage"          # Can store documents
    SEARCH = "search"            # Can search documents
    EXPORT = "export"            # Can export documents
    UI = "ui"                    # Provides UI components
    API = "api"                  # Provides API endpoints
    CLI = "cli"                  # Provides CLI commands
    WEBHOOK = "webhook"          # Can handle webhooks
    NOTIFICATION = "notification" # Can send notifications


class PluginHook(Enum):
    """Plugin hook points"""
    # Document lifecycle hooks
    BEFORE_SCAN = "before_scan"
    AFTER_SCAN = "after_scan"
    BEFORE_INDEX = "before_index"
    AFTER_INDEX = "after_index"
    BEFORE_STORE = "before_store"
    AFTER_STORE = "after_store"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"
    
    # Search hooks
    BEFORE_SEARCH = "before_search"
    AFTER_SEARCH = "after_search"
    MODIFY_RESULTS = "modify_results"
    
    # System hooks
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    CONFIG_CHANGE = "config_change"
    
    # UI hooks
    UI_MENU = "ui_menu"
    UI_TOOLBAR = "ui_toolbar"
    UI_SIDEBAR = "ui_sidebar"


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    author: str
    description: str
    website: Optional[str] = None
    license: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[PluginCapability] = field(default_factory=list)
    hooks: List[PluginHook] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    min_docscope_version: Optional[str] = None
    max_docscope_version: Optional[str] = None


class Plugin(ABC):
    """Base class for DocScope plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize plugin with configuration"""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = True
        self._hooks = {}
        self._commands = {}
        self._api_routes = []
        
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin
        Returns True if initialization was successful
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup when plugin is disabled or application shuts down"""
        pass
    
    def validate_config(self) -> bool:
        """
        Validate plugin configuration
        Returns True if configuration is valid
        """
        metadata = self.get_metadata()
        schema = metadata.config_schema
        
        if not schema:
            return True
        
        # Basic validation
        for key, spec in schema.items():
            required = spec.get('required', False)
            if required and key not in self.config:
                self.logger.error(f"Required configuration key missing: {key}")
                return False
            
            if key in self.config:
                value = self.config[key]
                expected_type = spec.get('type')
                if expected_type and not isinstance(value, expected_type):
                    self.logger.error(
                        f"Configuration key {key} has wrong type. "
                        f"Expected {expected_type}, got {type(value)}"
                    )
                    return False
        
        return True
    
    def register_hook(self, hook: PluginHook, handler: Callable) -> None:
        """Register a hook handler"""
        if hook not in self._hooks:
            self._hooks[hook] = []
        self._hooks[hook].append(handler)
    
    def get_hooks(self) -> Dict[PluginHook, List[Callable]]:
        """Get all registered hooks"""
        return self._hooks
    
    def register_command(self, name: str, handler: Callable, description: str = "") -> None:
        """Register a CLI command"""
        self._commands[name] = {
            'handler': handler,
            'description': description
        }
    
    def get_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered commands"""
        return self._commands
    
    def register_api_route(self, path: str, method: str, handler: Callable) -> None:
        """Register an API route"""
        self._api_routes.append({
            'path': path,
            'method': method,
            'handler': handler
        })
    
    def get_api_routes(self) -> List[Dict[str, Any]]:
        """Get all registered API routes"""
        return self._api_routes
    
    def on_enable(self) -> None:
        """Called when plugin is enabled"""
        self.enabled = True
        self.logger.info(f"Plugin {self.get_metadata().name} enabled")
    
    def on_disable(self) -> None:
        """Called when plugin is disabled"""
        self.enabled = False
        self.logger.info(f"Plugin {self.get_metadata().name} disabled")
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status information"""
        metadata = self.get_metadata()
        return {
            'name': metadata.name,
            'version': metadata.version,
            'enabled': self.enabled,
            'capabilities': [c.value for c in metadata.capabilities],
            'hooks': [h.value for h in metadata.hooks],
            'commands': list(self._commands.keys()),
            'api_routes': len(self._api_routes)
        }


class ScannerPlugin(Plugin):
    """Base class for scanner plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_formats = []
    
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this plugin can handle the given file"""
        pass
    
    @abstractmethod
    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan a file and return document data
        Returns dict with: title, content, metadata, format
        """
        pass
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return self.supported_formats


class ProcessorPlugin(Plugin):
    """Base class for document processor plugins"""
    
    @abstractmethod
    def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document and return modified version
        Can modify content, add metadata, extract entities, etc.
        """
        pass
    
    def should_process(self, document: Dict[str, Any]) -> bool:
        """Check if this processor should handle the document"""
        return True


class StoragePlugin(Plugin):
    """Base class for storage backend plugins"""
    
    @abstractmethod
    def store_document(self, document: Dict[str, Any]) -> str:
        """Store a document and return its ID"""
        pass
    
    @abstractmethod
    def retrieve_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID"""
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        pass
    
    @abstractmethod
    def list_documents(self, **filters) -> List[Dict[str, Any]]:
        """List documents with optional filters"""
        pass


class SearchPlugin(Plugin):
    """Base class for search backend plugins"""
    
    @abstractmethod
    def index_document(self, document: Dict[str, Any]) -> bool:
        """Index a document for searching"""
        pass
    
    @abstractmethod
    def search(self, query: str, **options) -> List[Dict[str, Any]]:
        """Search for documents"""
        pass
    
    @abstractmethod
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index"""
        pass
    
    def get_suggestions(self, query: str) -> List[str]:
        """Get search suggestions"""
        return []


class ExportPlugin(Plugin):
    """Base class for export plugins"""
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats"""
        pass
    
    @abstractmethod
    def export_documents(self, documents: List[Dict[str, Any]], 
                        format: str, options: Dict[str, Any] = None) -> bytes:
        """Export documents to the specified format"""
        pass
    
    def can_export(self, format: str) -> bool:
        """Check if this plugin can export to the given format"""
        return format in self.get_supported_formats()


class NotificationPlugin(Plugin):
    """Base class for notification plugins"""
    
    @abstractmethod
    def send_notification(self, message: str, level: str = "info", 
                         **options) -> bool:
        """Send a notification"""
        pass
    
    def get_notification_types(self) -> List[str]:
        """Get supported notification types"""
        return ["info", "warning", "error", "success"]