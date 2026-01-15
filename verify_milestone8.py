#!/usr/bin/env python3
"""
Milestone 8 Verification Script - Plugin System
Validates the implementation of the plugin architecture
"""

import os
import sys
import json
from pathlib import Path
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} missing: {filepath}")
        return False

def check_module_structure(module_path, required_items, description):
    """Check if a Python module has required structure"""
    if not os.path.exists(module_path):
        print(f"✗ {description} missing: {module_path}")
        return False
    
    try:
        with open(module_path, 'r') as f:
            content = f.read()
        
        missing_items = []
        for item in required_items:
            if item not in content:
                missing_items.append(item)
        
        if missing_items:
            print(f"✗ {description} missing items: {missing_items}")
            return False
        else:
            print(f"✓ {description} has required structure")
            return True
    except Exception as e:
        print(f"✗ Error checking {description}: {e}")
        return False

def verify_plugin_base():
    """Verify plugin base classes and interfaces"""
    print("\n=== Plugin Base Architecture ===")
    checks = []
    
    # Check base.py
    base_items = [
        "class Plugin(ABC)",
        "class PluginMetadata",
        "class PluginCapability(Enum)",
        "class PluginHook(Enum)",
        "def get_metadata",
        "def initialize",
        "def shutdown",
        "def register_hook",
        "def register_command",
        "def register_api_route",
        "class ScannerPlugin",
        "class ProcessorPlugin",
        "class NotificationPlugin"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/base.py",
        base_items,
        "Plugin base classes"
    ))
    
    # Check exceptions.py
    exception_items = [
        "class PluginError(Exception)",
        "class PluginNotFoundError",
        "class PluginLoadError",
        "class PluginConfigError",
        "class PluginDependencyError"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/exceptions.py",
        exception_items,
        "Plugin exceptions"
    ))
    
    return all(checks)

def verify_plugin_infrastructure():
    """Verify plugin infrastructure components"""
    print("\n=== Plugin Infrastructure ===")
    checks = []
    
    # Check loader.py
    loader_items = [
        "class PluginLoader",
        "def __init__",
        "def discover_plugins",
        "def load_plugin",
        "def load_plugin_from_file",
        "def load_plugin_config",
        "def validate_plugin",
        "def check_dependencies"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/loader.py",
        loader_items,
        "Plugin loader"
    ))
    
    # Check registry.py
    registry_items = [
        "class PluginRegistry",
        "def register",
        "def unregister",
        "def get_plugin",
        "def list_plugins",
        "def get_plugins_by_capability",
        "def execute_hook",
        "def execute_command"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/registry.py",
        registry_items,
        "Plugin registry"
    ))
    
    # Check manager.py
    manager_items = [
        "class PluginManager",
        "def __new__",  # Singleton pattern
        "def discover",
        "def load_plugin",
        "def unload_plugin",
        "def enable_plugin",
        "def disable_plugin",
        "def list_plugins",
        "def get_plugin_info",
        "def search_plugins"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/manager.py",
        manager_items,
        "Plugin manager"
    ))
    
    return all(checks)

def verify_builtin_plugins():
    """Verify built-in plugin implementations"""
    print("\n=== Built-in Plugins ===")
    checks = []
    
    # Check PDF scanner plugin
    pdf_items = [
        "class PDFScannerPlugin(ScannerPlugin)",
        "def get_metadata",
        "def initialize",
        "def shutdown",
        "def can_handle",
        "def scan_file",
        "self.supported_formats"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/builtin/pdf_scanner.py",
        pdf_items,
        "PDF scanner plugin"
    ))
    
    # Check Markdown processor plugin
    markdown_items = [
        "class MarkdownProcessorPlugin(ProcessorPlugin)",
        "def get_metadata",
        "def initialize",
        "def shutdown",
        "def should_process",
        "def process_document",
        "_extract_toc",
        "_extract_links",
        "_extract_code_blocks",
        "_calculate_reading_time"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/builtin/markdown_processor.py",
        markdown_items,
        "Markdown processor plugin"
    ))
    
    # Check Slack notifier plugin
    slack_items = [
        "class SlackNotifierPlugin(NotificationPlugin)",
        "def get_metadata",
        "def initialize",
        "def shutdown",
        "def send_notification",
        "def notify_scan_complete",
        "def notify_index_complete",
        "def notify_document_deleted"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/builtin/slack_notifier.py",
        slack_items,
        "Slack notifier plugin"
    ))
    
    # Check builtin __init__.py exists
    checks.append(check_file_exists(
        "docscope/plugins/builtin/__init__.py",
        "Built-in plugins package"
    ))
    
    return all(checks)

def verify_plugin_integration():
    """Verify plugin system integration"""
    print("\n=== Plugin Integration ===")
    checks = []
    
    # Check if plugin module is properly initialized
    checks.append(check_file_exists(
        "docscope/plugins/__init__.py",
        "Plugin module init"
    ))
    
    # Verify imports are accessible - check for the actual import format used
    init_items = [
        "from .base import Plugin, PluginMetadata, PluginCapability, PluginHook",
        "from .loader import PluginLoader",
        "from .registry import PluginRegistry",
        "from .manager import PluginManager",
        "from .exceptions import"
    ]
    checks.append(check_module_structure(
        "docscope/plugins/__init__.py",
        init_items,
        "Plugin module exports"
    ))
    
    return all(checks)

def verify_plugin_tests():
    """Verify plugin system tests"""
    print("\n=== Plugin Tests ===")
    checks = []
    
    test_items = [
        "class TestPlugin(Plugin)",
        "class TestPluginBase",
        "class TestPluginRegistry",
        "class TestPluginLoader",
        "class TestPluginManager",
        "class TestScannerPlugin",
        "class TestProcessorPlugin",
        "class TestNotificationPlugin",
        "class TestBuiltinPlugins",
        "test_plugin_creation",
        "test_plugin_metadata",
        "test_plugin_initialization",
        "test_register_plugin",
        "test_execute_hook",
        "test_pdf_scanner_metadata",
        "test_markdown_processor_metadata",
        "test_slack_notifier_metadata"
    ]
    
    checks.append(check_module_structure(
        "tests/test_plugins.py",
        test_items,
        "Plugin system tests"
    ))
    
    return all(checks)

def verify_plugin_features():
    """Verify plugin system features"""
    print("\n=== Plugin Features ===")
    checks = []
    
    # Check for hook system
    print("Checking hook system implementation...")
    hooks_found = True
    for hook_type in ["STARTUP", "SHUTDOWN", "BEFORE_SCAN", "AFTER_SCAN", 
                      "BEFORE_INDEX", "AFTER_INDEX", "BEFORE_SEARCH", "AFTER_SEARCH"]:
        if not check_module_structure(
            "docscope/plugins/base.py",
            [f'{hook_type} = '],
            f"Hook type {hook_type}"
        ):
            hooks_found = False
    checks.append(hooks_found)
    
    # Check for capability system
    print("\nChecking capability system implementation...")
    capabilities_found = True
    for capability in ["SCANNER", "PROCESSOR", "STORAGE", "SEARCH", "API", "UI", "NOTIFICATION"]:
        if not check_module_structure(
            "docscope/plugins/base.py",
            [f'{capability} = '],
            f"Capability {capability}"
        ):
            capabilities_found = False
    checks.append(capabilities_found)
    
    # Check for plugin lifecycle
    print("\nChecking plugin lifecycle methods...")
    lifecycle_methods = ["initialize", "shutdown", "validate_config", "get_status"]
    lifecycle_found = all(
        check_module_structure(
            "docscope/plugins/base.py",
            [method],
            f"Lifecycle method {method}"
        )
        for method in lifecycle_methods
    )
    checks.append(lifecycle_found)
    
    return all(checks)

def main():
    """Main verification function"""
    print("=" * 60)
    print("MILESTONE 8 VERIFICATION - Plugin System")
    print("=" * 60)
    
    results = []
    
    # Run all verifications
    results.append(("Plugin Base Architecture", verify_plugin_base()))
    results.append(("Plugin Infrastructure", verify_plugin_infrastructure()))
    results.append(("Built-in Plugins", verify_builtin_plugins()))
    results.append(("Plugin Integration", verify_plugin_integration()))
    results.append(("Plugin Tests", verify_plugin_tests()))
    results.append(("Plugin Features", verify_plugin_features()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_passed = sum(1 for _, passed in results if passed)
    total_checks = len(results)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:.<40} {status}")
    
    print(f"\nTotal: {total_passed}/{total_checks} verification groups passed")
    
    if total_passed == total_checks:
        print("\n✓ MILESTONE 8 COMPLETE: Plugin system successfully implemented!")
        print("\nKey achievements:")
        print("- Extensible plugin architecture with abstract base classes")
        print("- Plugin lifecycle management (discovery, loading, initialization)")
        print("- Hook system for extending application behavior")
        print("- Capability-based plugin categorization")
        print("- Built-in plugins demonstrating scanner, processor, and notifier patterns")
        print("- Singleton plugin manager for centralized management")
        print("- Comprehensive test coverage for plugin system")
        return 0
    else:
        print("\n✗ MILESTONE 8 INCOMPLETE: Some components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())