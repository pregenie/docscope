"""Tests for Plugin System"""

import pytest
from pathlib import Path
from typing import Dict, Any

from docscope.plugins import (
    Plugin,
    PluginMetadata,
    PluginCapability,
    PluginHook,
    PluginManager,
    PluginLoader,
    PluginRegistry,
    PluginError,
    PluginNotFoundError
)
from docscope.plugins.base import (
    ScannerPlugin,
    ProcessorPlugin,
    NotificationPlugin
)
from docscope.core.config import Config


# Test plugin implementation
class TestPlugin(Plugin):
    """Simple test plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin for unit tests",
            capabilities=[PluginCapability.PROCESSOR],
            hooks=[PluginHook.STARTUP, PluginHook.SHUTDOWN]
        )
    
    def initialize(self) -> bool:
        self.initialized = True
        return True
    
    def shutdown(self) -> None:
        self.initialized = False


@pytest.fixture
def config():
    """Create test configuration"""
    return Config()


@pytest.fixture
def plugin_manager(config):
    """Create plugin manager for testing"""
    return PluginManager(config)


@pytest.fixture
def test_plugin():
    """Create test plugin instance"""
    return TestPlugin()


class TestPluginBase:
    """Test Plugin base class"""
    
    def test_plugin_creation(self):
        """Test creating a plugin"""
        plugin = TestPlugin()
        assert plugin is not None
        assert plugin.enabled == True
    
    def test_plugin_metadata(self):
        """Test plugin metadata"""
        plugin = TestPlugin()
        metadata = plugin.get_metadata()
        
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert PluginCapability.PROCESSOR in metadata.capabilities
        assert PluginHook.STARTUP in metadata.hooks
    
    def test_plugin_initialization(self):
        """Test plugin initialization"""
        plugin = TestPlugin()
        assert plugin.initialize() == True
        assert hasattr(plugin, 'initialized')
        assert plugin.initialized == True
    
    def test_plugin_shutdown(self):
        """Test plugin shutdown"""
        plugin = TestPlugin()
        plugin.initialize()
        plugin.shutdown()
        assert plugin.initialized == False
    
    def test_plugin_config_validation(self):
        """Test plugin configuration validation"""
        plugin = TestPlugin({'test_key': 'test_value'})
        assert plugin.validate_config() == True
    
    def test_plugin_hooks(self):
        """Test plugin hook registration"""
        plugin = TestPlugin()
        
        def test_handler():
            return "test"
        
        plugin.register_hook(PluginHook.STARTUP, test_handler)
        hooks = plugin.get_hooks()
        
        assert PluginHook.STARTUP in hooks
        assert test_handler in hooks[PluginHook.STARTUP]
    
    def test_plugin_commands(self):
        """Test plugin command registration"""
        plugin = TestPlugin()
        
        def test_command():
            return "executed"
        
        plugin.register_command("test", test_command, "Test command")
        commands = plugin.get_commands()
        
        assert "test" in commands
        assert commands["test"]["handler"] == test_command
        assert commands["test"]["description"] == "Test command"
    
    def test_plugin_api_routes(self):
        """Test plugin API route registration"""
        plugin = TestPlugin()
        
        def test_handler():
            return {"status": "ok"}
        
        plugin.register_api_route("/test", "GET", test_handler)
        routes = plugin.get_api_routes()
        
        assert len(routes) == 1
        assert routes[0]["path"] == "/test"
        assert routes[0]["method"] == "GET"
        assert routes[0]["handler"] == test_handler
    
    def test_plugin_status(self):
        """Test plugin status"""
        plugin = TestPlugin()
        status = plugin.get_status()
        
        assert status["name"] == "test_plugin"
        assert status["version"] == "1.0.0"
        assert status["enabled"] == True
        assert "capabilities" in status
        assert "hooks" in status


class TestPluginRegistry:
    """Test Plugin Registry"""
    
    def test_registry_creation(self):
        """Test creating a registry"""
        registry = PluginRegistry()
        assert registry is not None
        assert len(registry.plugins) == 0
    
    def test_register_plugin(self):
        """Test registering a plugin"""
        registry = PluginRegistry()
        plugin = TestPlugin()
        
        registry.register(plugin)
        
        assert "test_plugin" in registry.plugins
        assert registry.plugins["test_plugin"] == plugin
    
    def test_unregister_plugin(self):
        """Test unregistering a plugin"""
        registry = PluginRegistry()
        plugin = TestPlugin()
        
        registry.register(plugin)
        registry.unregister("test_plugin")
        
        assert "test_plugin" not in registry.plugins
    
    def test_get_plugin(self):
        """Test getting a plugin"""
        registry = PluginRegistry()
        plugin = TestPlugin()
        
        registry.register(plugin)
        retrieved = registry.get_plugin("test_plugin")
        
        assert retrieved == plugin
    
    def test_get_nonexistent_plugin(self):
        """Test getting non-existent plugin raises error"""
        registry = PluginRegistry()
        
        with pytest.raises(PluginNotFoundError):
            registry.get_plugin("nonexistent")
    
    def test_list_plugins(self):
        """Test listing plugins"""
        registry = PluginRegistry()
        plugin1 = TestPlugin()
        plugin2 = TestPlugin()
        plugin2.get_metadata = lambda: PluginMetadata(
            name="test_plugin2",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        
        registry.register(plugin1)
        registry.register(plugin2)
        
        plugins = registry.list_plugins()
        assert len(plugins) == 2
        assert "test_plugin" in plugins
        assert "test_plugin2" in plugins
    
    def test_execute_hook(self):
        """Test executing hooks"""
        registry = PluginRegistry()
        plugin = TestPlugin()
        
        results = []
        def test_handler(value):
            results.append(value)
            return value * 2
        
        plugin.register_hook(PluginHook.STARTUP, test_handler)
        registry.register(plugin)
        
        hook_results = registry.execute_hook(PluginHook.STARTUP, 5)
        
        assert len(results) == 1
        assert results[0] == 5
        assert hook_results[0] == 10
    
    def test_execute_command(self):
        """Test executing plugin commands"""
        registry = PluginRegistry()
        plugin = TestPlugin()
        
        def test_command(x, y):
            return x + y
        
        plugin.register_command("add", test_command, "Add two numbers")
        registry.register(plugin)
        
        result = registry.execute_command("test_plugin:add", 3, 4)
        assert result == 7
    
    def test_get_plugins_by_capability(self):
        """Test getting plugins by capability"""
        registry = PluginRegistry()
        plugin = TestPlugin()
        
        registry.register(plugin)
        
        processors = registry.get_plugins_by_capability(PluginCapability.PROCESSOR)
        assert len(processors) == 1
        assert processors[0] == plugin
        
        scanners = registry.get_plugins_by_capability(PluginCapability.SCANNER)
        assert len(scanners) == 0


class TestPluginLoader:
    """Test Plugin Loader"""
    
    def test_loader_creation(self, config):
        """Test creating a loader"""
        loader = PluginLoader(config)
        assert loader is not None
        assert len(loader.plugin_dirs) > 0
    
    def test_discover_plugins(self, config):
        """Test discovering plugins"""
        loader = PluginLoader(config)
        plugins = loader.discover_plugins()
        
        # Should find built-in plugins at least
        assert isinstance(plugins, list)
    
    def test_load_plugin_config(self, config):
        """Test loading plugin configuration"""
        loader = PluginLoader(config)
        config = loader.load_plugin_config("test_plugin")
        
        assert isinstance(config, dict)


class TestPluginManager:
    """Test Plugin Manager"""
    
    def test_manager_singleton(self, config):
        """Test manager is singleton"""
        manager1 = PluginManager(config)
        manager2 = PluginManager(config)
        assert manager1 is manager2
    
    def test_discover_plugins(self, plugin_manager):
        """Test discovering plugins"""
        plugins = plugin_manager.discover()
        assert isinstance(plugins, list)
    
    def test_list_plugins(self, plugin_manager):
        """Test listing plugins"""
        plugins = plugin_manager.list_plugins()
        assert isinstance(plugins, list)
        
        for plugin in plugins:
            assert 'name' in plugin
            assert 'loaded' in plugin
            assert 'enabled' in plugin
    
    def test_get_plugin_info(self, plugin_manager):
        """Test getting plugin information"""
        # This would require a real plugin to be available
        pass
    
    def test_search_plugins(self, plugin_manager):
        """Test searching plugins"""
        results = plugin_manager.search_plugins("test")
        assert isinstance(results, list)
    
    def test_get_status(self, plugin_manager):
        """Test getting manager status"""
        status = plugin_manager.get_status()
        
        assert 'discovered' in status
        assert 'loaded' in status
        assert 'registry' in status
        assert 'plugin_directories' in status


class TestScannerPlugin:
    """Test Scanner Plugin base class"""
    
    def test_scanner_plugin_interface(self):
        """Test scanner plugin interface"""
        class TestScanner(ScannerPlugin):
            def get_metadata(self):
                return PluginMetadata(
                    name="test_scanner",
                    version="1.0.0",
                    author="Test",
                    description="Test scanner"
                )
            
            def initialize(self):
                return True
            
            def shutdown(self):
                pass
            
            def can_handle(self, file_path):
                return file_path.suffix == '.test'
            
            def scan_file(self, file_path):
                return {
                    'title': file_path.stem,
                    'content': 'test content',
                    'format': 'test'
                }
        
        scanner = TestScanner()
        assert scanner.can_handle(Path('test.test'))
        assert not scanner.can_handle(Path('test.txt'))
        
        result = scanner.scan_file(Path('test.test'))
        assert result['format'] == 'test'


class TestProcessorPlugin:
    """Test Processor Plugin base class"""
    
    def test_processor_plugin_interface(self):
        """Test processor plugin interface"""
        class TestProcessor(ProcessorPlugin):
            def get_metadata(self):
                return PluginMetadata(
                    name="test_processor",
                    version="1.0.0",
                    author="Test",
                    description="Test processor"
                )
            
            def initialize(self):
                return True
            
            def shutdown(self):
                pass
            
            def process_document(self, document):
                document['processed'] = True
                return document
        
        processor = TestProcessor()
        doc = {'title': 'test'}
        result = processor.process_document(doc)
        
        assert result['processed'] == True
        assert result['title'] == 'test'


class TestNotificationPlugin:
    """Test Notification Plugin base class"""
    
    def test_notification_plugin_interface(self):
        """Test notification plugin interface"""
        class TestNotifier(NotificationPlugin):
            def get_metadata(self):
                return PluginMetadata(
                    name="test_notifier",
                    version="1.0.0",
                    author="Test",
                    description="Test notifier"
                )
            
            def initialize(self):
                return True
            
            def shutdown(self):
                pass
            
            def send_notification(self, message, level="info", **options):
                return True
        
        notifier = TestNotifier()
        result = notifier.send_notification("Test message", level="info")
        assert result == True
        
        types = notifier.get_notification_types()
        assert "info" in types


class TestBuiltinPlugins:
    """Test built-in plugins"""
    
    def test_pdf_scanner_metadata(self):
        """Test PDF scanner plugin metadata"""
        from docscope.plugins.builtin.pdf_scanner import PDFScannerPlugin
        
        plugin = PDFScannerPlugin()
        metadata = plugin.get_metadata()
        
        assert metadata.name == "pdf_scanner"
        assert PluginCapability.SCANNER in metadata.capabilities
        assert ".pdf" in plugin.supported_formats
    
    def test_markdown_processor_metadata(self):
        """Test Markdown processor plugin metadata"""
        from docscope.plugins.builtin.markdown_processor import MarkdownProcessorPlugin
        
        plugin = MarkdownProcessorPlugin()
        metadata = plugin.get_metadata()
        
        assert metadata.name == "markdown_processor"
        assert PluginCapability.PROCESSOR in metadata.capabilities
        assert PluginHook.BEFORE_INDEX in metadata.hooks
    
    def test_slack_notifier_metadata(self):
        """Test Slack notifier plugin metadata"""
        from docscope.plugins.builtin.slack_notifier import SlackNotifierPlugin
        
        plugin = SlackNotifierPlugin({'webhook_url': 'test'})
        metadata = plugin.get_metadata()
        
        assert metadata.name == "slack_notifier"
        assert PluginCapability.NOTIFICATION in metadata.capabilities
        assert PluginHook.AFTER_SCAN in metadata.hooks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])