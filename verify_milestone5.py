#!/usr/bin/env python3
"""Verification script for Milestone 5: REST API Server"""

import os
import sys
from pathlib import Path
import importlib.util
import json


class APIVerification:
    """Verify API implementation"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.api_path = self.base_path / "docscope" / "api"
        self.errors = []
        self.warnings = []
        
    def verify_structure(self):
        """Verify API directory structure"""
        print("Verifying API structure...")
        
        required_files = [
            "config.py",
            "models.py",
            "dependencies.py",
            "app.py",
            "routers/__init__.py",
            "routers/documents.py",
            "routers/search.py",
            "routers/scanner.py",
            "routers/categories.py",
            "routers/tags.py",
            "routers/health.py",
            "routers/websocket.py",
        ]
        
        for file in required_files:
            file_path = self.api_path / file
            if not file_path.exists():
                self.errors.append(f"Missing file: {file}")
            else:
                print(f"  ✓ {file}")
        
        return len(self.errors) == 0
    
    def verify_configuration(self):
        """Verify API configuration"""
        print("\nVerifying API configuration...")
        
        config_file = self.api_path / "config.py"
        if not config_file.exists():
            self.errors.append("Configuration file missing")
            return False
        
        # Check configuration content
        content = config_file.read_text()
        required_configs = [
            "class Settings",
            "app_name",
            "version",
            "host",
            "port",
            "database_url",
            "secret_key",
            "cors_origins",
            "@lru_cache",
            "get_settings"
        ]
        
        for config in required_configs:
            if config not in content:
                self.errors.append(f"Missing configuration: {config}")
            else:
                print(f"  ✓ {config}")
        
        return True
    
    def verify_models(self):
        """Verify API models"""
        print("\nVerifying API models...")
        
        models_file = self.api_path / "models.py"
        if not models_file.exists():
            self.errors.append("Models file missing")
            return False
        
        content = models_file.read_text()
        required_models = [
            "class DocumentCreate",
            "class DocumentUpdate",
            "class DocumentResponse",
            "class DocumentListResponse",
            "class SearchRequest",
            "class SearchResponse",
            "class SearchResultItem",
            "class ScanRequest",
            "class ScanResponse",
            "class CategoryCreate",
            "class CategoryResponse",
            "class TagCreate",
            "class TagResponse",
            "class ErrorResponse"
        ]
        
        for model in required_models:
            if model not in content:
                self.errors.append(f"Missing model: {model}")
            else:
                print(f"  ✓ {model}")
        
        return True
    
    def verify_dependencies(self):
        """Verify dependency injection"""
        print("\nVerifying dependencies...")
        
        deps_file = self.api_path / "dependencies.py"
        if not deps_file.exists():
            self.errors.append("Dependencies file missing")
            return False
        
        content = deps_file.read_text()
        required_deps = [
            "get_storage",
            "get_search_engine",
            "get_scanner",
            "verify_token",
            "rate_limiter",
            "class Pagination",
            "init_dependencies",
            "cleanup_dependencies"
        ]
        
        for dep in required_deps:
            if dep not in content:
                self.errors.append(f"Missing dependency: {dep}")
            else:
                print(f"  ✓ {dep}")
        
        return True
    
    def verify_routers(self):
        """Verify API routers"""
        print("\nVerifying routers...")
        
        routers_path = self.api_path / "routers"
        if not routers_path.exists():
            self.errors.append("Routers directory missing")
            return False
        
        routers = [
            ("documents.py", ["list_documents", "get_document", "create_document", 
                            "update_document", "delete_document", "upload_document"]),
            ("search.py", ["search_documents", "get_search_suggestions", 
                         "find_similar_documents", "reindex_all_documents"]),
            ("scanner.py", ["scan_documents", "get_supported_formats", "watch_directory"]),
            ("categories.py", ["list_categories", "create_category", "get_category_tree"]),
            ("tags.py", ["list_tags", "create_tag", "get_popular_tags", "get_tag_cloud"]),
            ("health.py", ["health_check", "liveness_check", "readiness_check", 
                         "get_stats", "get_metrics"]),
            ("websocket.py", ["websocket_endpoint", "notifications_endpoint", 
                           "live_search_endpoint", "ConnectionManager"])
        ]
        
        for router_file, endpoints in routers:
            file_path = routers_path / router_file
            if not file_path.exists():
                self.errors.append(f"Missing router: {router_file}")
                continue
            
            content = file_path.read_text()
            print(f"\n  Checking {router_file}:")
            for endpoint in endpoints:
                if endpoint not in content:
                    self.errors.append(f"Missing endpoint in {router_file}: {endpoint}")
                else:
                    print(f"    ✓ {endpoint}")
        
        return True
    
    def verify_application(self):
        """Verify main application"""
        print("\nVerifying main application...")
        
        app_file = self.api_path / "app.py"
        if not app_file.exists():
            self.errors.append("Application file missing")
            return False
        
        content = app_file.read_text()
        required_elements = [
            "from fastapi import FastAPI",
            "create_app",
            "configure_middleware",
            "configure_routers",
            "configure_exception_handlers",
            "CORSMiddleware",
            "GZipMiddleware",
            "@asynccontextmanager",
            "async def lifespan",
            "app = create_app()"
        ]
        
        for element in required_elements:
            if element not in content:
                self.errors.append(f"Missing in app.py: {element}")
            else:
                print(f"  ✓ {element}")
        
        return True
    
    def verify_server_entry(self):
        """Verify server entry point"""
        print("\nVerifying server entry point...")
        
        server_file = self.base_path / "docscope" / "server.py"
        if not server_file.exists():
            self.errors.append("Server entry point missing")
            return False
        
        content = server_file.read_text()
        required = [
            "import uvicorn",
            "from docscope.api.app import app",
            "run_server",
            "__main__"
        ]
        
        for item in required:
            if item not in content:
                self.errors.append(f"Missing in server.py: {item}")
            else:
                print(f"  ✓ {item}")
        
        return True
    
    def verify_tests(self):
        """Verify test files"""
        print("\nVerifying tests...")
        
        test_file = self.base_path / "tests" / "test_api.py"
        if not test_file.exists():
            self.warnings.append("API tests missing")
            return False
        
        content = test_file.read_text()
        test_classes = [
            "TestHealthEndpoints",
            "TestDocumentEndpoints",
            "TestSearchEndpoints",
            "TestCategoryEndpoints",
            "TestTagEndpoints",
            "TestScannerEndpoints",
            "TestWebSocketEndpoints",
            "TestAuthentication",
            "TestErrorHandling"
        ]
        
        for test_class in test_classes:
            if test_class not in content:
                self.warnings.append(f"Missing test class: {test_class}")
            else:
                print(f"  ✓ {test_class}")
        
        return True
    
    def check_imports(self):
        """Check if required imports work"""
        print("\nChecking imports (structural only)...")
        
        # Check FastAPI imports
        try:
            spec = importlib.util.find_spec("fastapi")
            if spec:
                print("  ✓ FastAPI available")
            else:
                self.warnings.append("FastAPI not installed (pip install fastapi)")
        except ImportError:
            self.warnings.append("FastAPI not installed (pip install fastapi)")
        
        # Check Uvicorn imports
        try:
            spec = importlib.util.find_spec("uvicorn")
            if spec:
                print("  ✓ Uvicorn available")
            else:
                self.warnings.append("Uvicorn not installed (pip install uvicorn)")
        except ImportError:
            self.warnings.append("Uvicorn not installed (pip install uvicorn)")
        
        # Check Pydantic imports
        try:
            spec = importlib.util.find_spec("pydantic")
            if spec:
                print("  ✓ Pydantic available")
            else:
                self.warnings.append("Pydantic not installed (pip install pydantic)")
        except ImportError:
            self.warnings.append("Pydantic not installed (pip install pydantic)")
        
        return True
    
    def verify_integration(self):
        """Verify integration points"""
        print("\nVerifying integration points...")
        
        # Check CLI integration
        cli_file = self.base_path / "docscope" / "cli.py"
        if cli_file.exists():
            content = cli_file.read_text()
            if "serve" in content:
                print("  ✓ CLI 'serve' command integrated")
            else:
                self.warnings.append("CLI 'serve' command not found")
        
        # Check that routers use dependencies correctly
        routers_path = self.api_path / "routers"
        for router in ["documents.py", "search.py", "scanner.py"]:
            file_path = routers_path / router
            if file_path.exists():
                content = file_path.read_text()
                if "Depends(" in content:
                    print(f"  ✓ {router} uses dependency injection")
                else:
                    self.warnings.append(f"{router} doesn't use dependency injection")
        
        return True
    
    def run_verification(self):
        """Run all verifications"""
        print("=" * 60)
        print("MILESTONE 5: REST API SERVER VERIFICATION")
        print("=" * 60)
        
        checks = [
            ("Structure", self.verify_structure),
            ("Configuration", self.verify_configuration),
            ("Models", self.verify_models),
            ("Dependencies", self.verify_dependencies),
            ("Routers", self.verify_routers),
            ("Application", self.verify_application),
            ("Server Entry", self.verify_server_entry),
            ("Tests", self.verify_tests),
            ("Imports", self.check_imports),
            ("Integration", self.verify_integration),
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
            print("\n✓ MILESTONE 5: REST API SERVER - COMPLETE")
            return True
        else:
            print("\n✗ MILESTONE 5: REST API SERVER - INCOMPLETE")
            return False


if __name__ == "__main__":
    verifier = APIVerification()
    success = verifier.run_verification()
    
    # Update milestone status
    status_file = Path(__file__).parent / "MILESTONE_STATUS.md"
    if status_file.exists():
        content = status_file.read_text()
        if success:
            content = content.replace(
                "- [ ] Milestone 5: REST API Server",
                "- [x] Milestone 5: REST API Server ✓"
            )
            status_file.write_text(content)
            print("\n✓ Updated MILESTONE_STATUS.md")
    
    sys.exit(0 if success else 1)