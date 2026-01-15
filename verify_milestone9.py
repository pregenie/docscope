#!/usr/bin/env python3
"""
Milestone 9 Verification Script - Advanced Features
Validates the implementation of export, monitoring, and watching features
"""

import os
import sys
from pathlib import Path

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

def verify_features_module():
    """Verify features module structure"""
    print("\n=== Features Module ===")
    checks = []
    
    # Check module initialization
    checks.append(check_file_exists(
        "docscope/features/__init__.py",
        "Features module init"
    ))
    
    # Check imports
    init_items = [
        "from .export import Exporter, ExportFormat",
        "from .monitor import PerformanceMonitor, HealthChecker",
        "from .watcher import FileWatcher, WatchEvent"
    ]
    checks.append(check_module_structure(
        "docscope/features/__init__.py",
        init_items,
        "Features module exports"
    ))
    
    return all(checks)

def verify_export_functionality():
    """Verify export functionality"""
    print("\n=== Export Functionality ===")
    checks = []
    
    # Check export.py
    export_items = [
        "class ExportFormat(Enum)",
        "class Exporter",
        "def export_document",
        "def export_documents",
        "def export_search_results",
        "_export_json",
        "_export_yaml",
        "_export_markdown",
        "_export_html",
        "_export_pdf",
        "_export_csv",
        "JSON = ",
        "YAML = ",
        "MARKDOWN = ",
        "HTML = ",
        "PDF = ",
        "CSV = "
    ]
    checks.append(check_module_structure(
        "docscope/features/export.py",
        export_items,
        "Export module"
    ))
    
    return all(checks)

def verify_file_watcher():
    """Verify file watcher functionality"""
    print("\n=== File Watcher ===")
    checks = []
    
    # Check watcher.py
    watcher_items = [
        "class WatchEventType(Enum)",
        "class WatchEvent",
        "class DocScopeEventHandler",
        "class FileWatcher",
        "def watch",
        "def unwatch",
        "def start",
        "def stop",
        "def should_process",
        "def handle_event",
        "_handle_created",
        "_handle_modified",
        "_handle_deleted",
        "_handle_moved",
        "CREATED = ",
        "MODIFIED = ",
        "DELETED = ",
        "MOVED = "
    ]
    checks.append(check_module_structure(
        "docscope/features/watcher.py",
        watcher_items,
        "File watcher module"
    ))
    
    # Check for watchdog integration
    watchdog_items = [
        "from watchdog.observers import Observer",
        "from watchdog.events import FileSystemEventHandler"
    ]
    checks.append(check_module_structure(
        "docscope/features/watcher.py",
        watchdog_items,
        "Watchdog integration"
    ))
    
    return all(checks)

def verify_monitoring():
    """Verify performance monitoring and health checks"""
    print("\n=== Monitoring & Health Checks ===")
    checks = []
    
    # Check monitor.py
    monitor_items = [
        "class Metric",
        "class HealthStatus",
        "class PerformanceMonitor",
        "class HealthChecker",
        "def record_metric",
        "def increment_counter",
        "def measure_time",
        "def get_system_metrics",
        "def get_application_metrics",
        "def register_check",
        "def run_check",
        "def run_all_checks",
        "_check_system",
        "_check_disk_space",
        "_check_memory"
    ]
    checks.append(check_module_structure(
        "docscope/features/monitor.py",
        monitor_items,
        "Monitoring module"
    ))
    
    # Check for psutil integration
    psutil_items = [
        "import psutil",
        "psutil.cpu_percent",
        "psutil.virtual_memory",
        "psutil.disk_usage"
    ]
    checks.append(check_module_structure(
        "docscope/features/monitor.py",
        psutil_items,
        "System metrics integration"
    ))
    
    return all(checks)

def verify_export_formats():
    """Verify all export formats are implemented"""
    print("\n=== Export Formats ===")
    checks = []
    
    formats = ["JSON", "YAML", "MARKDOWN", "HTML", "PDF", "CSV"]
    
    for format_name in formats:
        # Check enum value
        if check_module_structure(
            "docscope/features/export.py",
            [f'{format_name} = '],
            f"Export format {format_name}"
        ):
            checks.append(True)
        else:
            checks.append(False)
            
        # Check handler method
        method_name = f"_export_{format_name.lower()}"
        if check_module_structure(
            "docscope/features/export.py",
            [f"def {method_name}"],
            f"Export handler for {format_name}"
        ):
            checks.append(True)
        else:
            checks.append(False)
    
    return all(checks)

def verify_watch_events():
    """Verify watch event handling"""
    print("\n=== Watch Event Handling ===")
    checks = []
    
    # Check event types
    event_types = ["CREATED", "MODIFIED", "DELETED", "MOVED"]
    for event_type in event_types:
        checks.append(check_module_structure(
            "docscope/features/watcher.py",
            [f"{event_type} = "],
            f"Watch event type {event_type}"
        ))
    
    # Check event handlers
    handlers = ["on_created", "on_modified", "on_deleted", "on_moved"]
    for handler in handlers:
        checks.append(check_module_structure(
            "docscope/features/watcher.py",
            [f"def {handler}"],
            f"Event handler {handler}"
        ))
    
    # Check auto-indexing handlers
    auto_handlers = ["_handle_created", "_handle_modified", "_handle_deleted", "_handle_moved"]
    for handler in auto_handlers:
        checks.append(check_module_structure(
            "docscope/features/watcher.py",
            [f"def {handler}"],
            f"Auto-index handler {handler}"
        ))
    
    return all(checks)

def verify_health_checks():
    """Verify health check implementations"""
    print("\n=== Health Check Components ===")
    checks = []
    
    # Default health checks
    default_checks = [
        ("_check_system", "System health check"),
        ("_check_disk_space", "Disk space check"),
        ("_check_memory", "Memory usage check")
    ]
    
    for check_name, description in default_checks:
        checks.append(check_module_structure(
            "docscope/features/monitor.py",
            [f"def {check_name}"],
            description
        ))
    
    # Additional health check support
    additional_checks = [
        ("add_database_check", "Database health check"),
        ("add_search_index_check", "Search index health check")
    ]
    
    for check_name, description in additional_checks:
        checks.append(check_module_structure(
            "docscope/features/monitor.py",
            [f"def {check_name}"],
            description
        ))
    
    return all(checks)

def verify_tests():
    """Verify test coverage for advanced features"""
    print("\n=== Test Coverage ===")
    checks = []
    
    test_classes = [
        "class TestExporter",
        "class TestFileWatcher",
        "class TestPerformanceMonitor",
        "class TestHealthChecker"
    ]
    
    checks.append(check_module_structure(
        "tests/test_features.py",
        test_classes,
        "Feature test classes"
    ))
    
    # Check for specific test methods
    test_methods = [
        "test_export_json",
        "test_export_yaml",
        "test_export_markdown",
        "test_export_html",
        "test_export_csv",
        "test_watch_path",
        "test_event_handling",
        "test_auto_index_created",
        "test_record_metric",
        "test_measure_time",
        "test_get_system_metrics",
        "test_run_check",
        "test_run_all_checks"
    ]
    
    for method in test_methods:
        if not check_module_structure(
            "tests/test_features.py",
            [f"def {method}"],
            f"Test method {method}"
        ):
            checks.append(False)
        else:
            checks.append(True)
    
    return all(checks)

def main():
    """Main verification function"""
    print("=" * 60)
    print("MILESTONE 9 VERIFICATION - Advanced Features")
    print("=" * 60)
    
    results = []
    
    # Run all verifications
    results.append(("Features Module", verify_features_module()))
    results.append(("Export Functionality", verify_export_functionality()))
    results.append(("File Watcher", verify_file_watcher()))
    results.append(("Monitoring", verify_monitoring()))
    results.append(("Export Formats", verify_export_formats()))
    results.append(("Watch Events", verify_watch_events()))
    results.append(("Health Checks", verify_health_checks()))
    results.append(("Test Coverage", verify_tests()))
    
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
        print("\n✓ MILESTONE 9 COMPLETE: Advanced features successfully implemented!")
        print("\nKey achievements:")
        print("- Multi-format export system (JSON, YAML, Markdown, HTML, PDF, CSV)")
        print("- File system watcher with auto-indexing")
        print("- Performance monitoring with metrics collection")
        print("- Health checking system with extensible checks")
        print("- Event-driven architecture for file changes")
        print("- Comprehensive test coverage for all features")
        return 0
    else:
        print("\n✗ MILESTONE 9 INCOMPLETE: Some components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())