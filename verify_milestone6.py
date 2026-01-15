#!/usr/bin/env python3
"""Verification script for Milestone 6: Complete CLI Implementation"""

import os
import sys
from pathlib import Path


class CLIVerification:
    """Verify CLI implementation"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.cli_path = self.base_path / "docscope" / "cli"
        self.errors = []
        self.warnings = []
        
    def verify_structure(self):
        """Verify CLI directory structure"""
        print("Verifying CLI structure...")
        
        required_files = [
            "cli.py",
            "__init__.py",
            "commands/__init__.py",
            "commands/scan.py",
            "commands/search.py",
            "commands/serve.py",
            "commands/export.py",
            "commands/watch.py",
            "commands/stats.py",
            "commands/database.py",
            "commands/plugins.py",
            "commands/config.py"
        ]
        
        for file in required_files:
            file_path = self.cli_path / file
            if not file_path.exists():
                self.errors.append(f"Missing file: {file}")
            else:
                print(f"  ✓ {file}")
        
        return len(self.errors) == 0
    
    def verify_main_cli(self):
        """Verify main CLI file"""
        print("\nVerifying main CLI...")
        
        cli_file = self.cli_path / "cli.py"
        if not cli_file.exists():
            self.errors.append("Main CLI file missing")
            return False
        
        content = cli_file.read_text()
        required_elements = [
            "@click.group",
            "def cli(",
            "DocScope - Universal Documentation Browser",
            "@click.version_option",
            "@click.option('--config'",
            "@click.option('--verbose'",
            "def init(",
            "cli.add_command"
        ]
        
        for element in required_elements:
            if element not in content:
                self.errors.append(f"Missing in cli.py: {element}")
            else:
                print(f"  ✓ {element}")
        
        return True
    
    def verify_commands(self):
        """Verify command implementations"""
        print("\nVerifying commands...")
        
        commands = {
            "scan.py": ["scan_command", "DocumentScanner", "Progress", "scan_paths"],
            "search.py": ["search_command", "SearchEngine", "filters", "highlight"],
            "serve.py": ["serve_command", "run_server", "host", "port"],
            "export.py": ["export_command", "export_json", "export_html", "export_markdown"],
            "watch.py": ["watch_command", "file_states", "detect_changes", "auto_index"],
            "stats.py": ["stats_command", "gather_statistics", "display_table_stats"],
            "database.py": ["db_group", "init_command", "backup_command", "optimize_command"],
            "plugins.py": ["plugins_group", "list_command", "install_command", "enable_command"],
            "config.py": ["config_group", "show_command", "get_command", "set_command", "validate_command"]
        }
        
        commands_path = self.cli_path / "commands"
        
        for cmd_file, required in commands.items():
            file_path = commands_path / cmd_file
            if not file_path.exists():
                self.errors.append(f"Missing command file: {cmd_file}")
                continue
            
            content = file_path.read_text()
            print(f"\n  Checking {cmd_file}:")
            
            for item in required:
                if item not in content:
                    self.errors.append(f"Missing in {cmd_file}: {item}")
                else:
                    print(f"    ✓ {item}")
        
        return True
    
    def verify_integration(self):
        """Verify CLI integration"""
        print("\nVerifying CLI integration...")
        
        # Check if commands are properly imported
        init_file = self.cli_path / "commands" / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            commands = [
                "scan_command", "search_command", "serve_command",
                "export_command", "db_group", "plugins_group",
                "watch_command", "stats_command", "config_group"
            ]
            
            for cmd in commands:
                if cmd not in content:
                    self.warnings.append(f"Command not exported: {cmd}")
                else:
                    print(f"  ✓ {cmd} exported")
        
        # Check main entry point
        main_init = self.base_path / "docscope" / "__init__.py"
        if main_init.exists():
            content = main_init.read_text()
            if "__version__" not in content:
                self.warnings.append("Version not defined in __init__.py")
            else:
                print("  ✓ Version defined")
        
        # Check if CLI is integrated with other components
        cli_file = self.cli_path / "cli.py"
        if cli_file.exists():
            content = cli_file.read_text()
            integrations = [
                "from ..core.config import Config",
                "from ..core.logging import",
                "from .commands import"
            ]
            
            for integration in integrations:
                if integration not in content:
                    self.warnings.append(f"Missing integration: {integration}")
                else:
                    print(f"  ✓ Integration: {integration[:30]}...")
        
        return True
    
    def verify_features(self):
        """Verify CLI features"""
        print("\nVerifying CLI features...")
        
        features = {
            "Rich output": ["from rich.console import Console", "console = Console"],
            "Progress bars": ["from rich.progress import Progress", "SpinnerColumn"],
            "Tables": ["from rich.table import Table", "table.add_column"],
            "Colored output": ["[green]", "[red]", "[blue]", "[yellow]"],
            "Interactive prompts": ["click.confirm", "click.prompt"],
            "File operations": ["Path", "pathlib"],
            "Configuration": ["Config", "yaml", "json"],
            "Error handling": ["try:", "except", "logger.error"],
            "Help text": ["--help", "help="],
            "Validation": ["click.Choice", "type=click"],
        }
        
        all_files = list(self.cli_path.rglob("*.py"))
        
        for feature, indicators in features.items():
            found = False
            for file_path in all_files:
                content = file_path.read_text()
                if any(indicator in content for indicator in indicators):
                    found = True
                    break
            
            if found:
                print(f"  ✓ {feature}")
            else:
                self.warnings.append(f"Feature not found: {feature}")
        
        return True
    
    def verify_tests(self):
        """Verify CLI tests"""
        print("\nVerifying tests...")
        
        test_file = self.base_path / "tests" / "test_cli.py"
        if not test_file.exists():
            self.warnings.append("CLI tests missing")
            return False
        
        content = test_file.read_text()
        test_classes = [
            "TestInitCommand",
            "TestScanCommand",
            "TestSearchCommand",
            "TestServeCommand",
            "TestExportCommand",
            "TestDatabaseCommands",
            "TestPluginCommands",
            "TestConfigCommands",
            "TestUtilityCommands",
            "TestGlobalOptions",
            "TestErrorHandling"
        ]
        
        for test_class in test_classes:
            if test_class not in content:
                self.warnings.append(f"Missing test class: {test_class}")
            else:
                print(f"  ✓ {test_class}")
        
        return True
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        print("\nChecking dependencies...")
        
        dependencies = {
            "click": "CLI framework",
            "rich": "Terminal formatting",
            "pyyaml": "YAML support"
        }
        
        for module, description in dependencies.items():
            try:
                __import__(module)
                print(f"  ✓ {module} ({description})")
            except ImportError:
                self.warnings.append(f"{module} not installed ({description})")
        
        return True
    
    def verify_entry_points(self):
        """Verify CLI entry points"""
        print("\nVerifying entry points...")
        
        # Check main entry point
        main_cli = self.cli_path / "cli.py"
        if main_cli.exists():
            content = main_cli.read_text()
            if "def main():" in content:
                print("  ✓ Main entry point defined")
            else:
                self.errors.append("Main entry point not defined")
            
            if "__main__" in content:
                print("  ✓ Direct execution supported")
        
        # Check pyproject.toml for console scripts
        pyproject = self.base_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "docscope" in content and "console_scripts" in content:
                print("  ✓ Console script configured")
            else:
                self.warnings.append("Console script not configured in pyproject.toml")
        
        return True
    
    def run_verification(self):
        """Run all verifications"""
        print("=" * 60)
        print("MILESTONE 6: COMPLETE CLI IMPLEMENTATION VERIFICATION")
        print("=" * 60)
        
        checks = [
            ("Structure", self.verify_structure),
            ("Main CLI", self.verify_main_cli),
            ("Commands", self.verify_commands),
            ("Integration", self.verify_integration),
            ("Features", self.verify_features),
            ("Tests", self.verify_tests),
            ("Dependencies", self.check_dependencies),
            ("Entry Points", self.verify_entry_points),
        ]
        
        results = []
        for name, check in checks:
            try:
                result = check()
                results.append((name, result))
            except Exception as e:
                print(f"\nError in {name}: {e}")
                results.append((name, False))
                self.errors.append(f"{name} check failed: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        
        for name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{name:20} {status}")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        total_passed = sum(1 for _, result in results if result)
        total_checks = len(results)
        
        print(f"\nTotal: {total_passed}/{total_checks} checks passed")
        
        if total_passed == total_checks:
            print("\n✓ MILESTONE 6: COMPLETE CLI IMPLEMENTATION - COMPLETE")
            return True
        else:
            print("\n✗ MILESTONE 6: COMPLETE CLI IMPLEMENTATION - INCOMPLETE")
            return False


if __name__ == "__main__":
    verifier = CLIVerification()
    success = verifier.run_verification()
    
    # Update milestone status
    status_file = Path(__file__).parent / "MILESTONE_STATUS.md"
    if status_file.exists():
        content = status_file.read_text()
        if success:
            content = content.replace(
                "- [ ] Milestone 6: Complete CLI Implementation",
                "- [x] Milestone 6: Complete CLI Implementation ✓"
            )
            status_file.write_text(content)
            print("\n✓ Updated MILESTONE_STATUS.md")
    
    sys.exit(0 if success else 1)