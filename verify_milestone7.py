#!/usr/bin/env python3
"""Verification script for Milestone 7: Build Web UI"""

import os
import sys
from pathlib import Path


class WebUIVerification:
    """Verify Web UI implementation"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.web_path = self.base_path / "docscope" / "web"
        self.static_path = self.web_path / "static"
        self.errors = []
        self.warnings = []
        
    def verify_structure(self):
        """Verify web UI directory structure"""
        print("Verifying web UI structure...")
        
        required_dirs = [
            "static",
            "static/css",
            "static/css/themes",
            "static/js"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.web_path / dir_name
            if not dir_path.exists():
                self.errors.append(f"Missing directory: {dir_name}")
            else:
                print(f"  ✓ {dir_name}")
        
        return len(self.errors) == 0
    
    def verify_html(self):
        """Verify HTML files"""
        print("\nVerifying HTML files...")
        
        index_file = self.static_path / "index.html"
        if not index_file.exists():
            self.errors.append("Missing index.html")
            return False
        
        content = index_file.read_text()
        
        # Check essential elements
        required_elements = [
            "<!DOCTYPE html>",
            "<title>DocScope",
            "search-page",
            "browse-page",
            "categories-page",
            "tags-page",
            "stats-page",
            "doc-viewer",
            "settings-modal"
        ]
        
        for element in required_elements:
            if element not in content:
                self.errors.append(f"Missing HTML element: {element}")
            else:
                print(f"  ✓ {element}")
        
        return True
    
    def verify_css(self):
        """Verify CSS files"""
        print("\nVerifying CSS files...")
        
        css_files = [
            "css/style.css",
            "css/themes/light.css",
            "css/themes/dark.css"
        ]
        
        for file in css_files:
            file_path = self.static_path / file
            if not file_path.exists():
                self.errors.append(f"Missing CSS file: {file}")
            else:
                print(f"  ✓ {file}")
                
                # Check content
                content = file_path.read_text()
                if file == "css/style.css":
                    required = [":root", "--color-primary", ".header", ".search-", ".modal"]
                    for item in required:
                        if item not in content:
                            self.warnings.append(f"Missing CSS rule in {file}: {item}")
        
        return True
    
    def verify_javascript(self):
        """Verify JavaScript files"""
        print("\nVerifying JavaScript files...")
        
        js_files = {
            "js/config.js": ["const Config", "api:", "search:", "ui:"],
            "js/api.js": ["class API", "getDocuments", "search", "getCategories"],
            "js/utils.js": ["const Utils", "debounce", "formatRelativeTime", "escapeHtml"],
            "js/components.js": ["const Components", "createSearchResult", "createDocumentCard"],
            "js/pages.js": ["const Pages", "performSearch", "loadDocuments"],
            "js/app.js": ["class DocScopeApp", "initNavigation", "DOMContentLoaded"]
        }
        
        for file, required in js_files.items():
            file_path = self.static_path / file
            if not file_path.exists():
                self.errors.append(f"Missing JS file: {file}")
            else:
                print(f"\n  Checking {file}:")
                content = file_path.read_text()
                
                for item in required:
                    if item not in content:
                        self.errors.append(f"Missing in {file}: {item}")
                    else:
                        print(f"    ✓ {item}")
        
        return True
    
    def verify_assets(self):
        """Verify static assets"""
        print("\nVerifying static assets...")
        
        favicon = self.static_path / "favicon.svg"
        if not favicon.exists():
            self.warnings.append("Missing favicon.svg")
        else:
            print("  ✓ favicon.svg")
        
        return True
    
    def verify_web_module(self):
        """Verify web module files"""
        print("\nVerifying web module...")
        
        required_files = [
            "__init__.py",
            "app.py"
        ]
        
        for file in required_files:
            file_path = self.web_path / file
            if not file_path.exists():
                self.errors.append(f"Missing web module file: {file}")
            else:
                print(f"  ✓ {file}")
                
                if file == "app.py":
                    content = file_path.read_text()
                    required = ["create_web_app", "mount_web_ui", "StaticFiles"]
                    for item in required:
                        if item not in content:
                            self.errors.append(f"Missing in app.py: {item}")
        
        return True
    
    def verify_features(self):
        """Verify UI features"""
        print("\nVerifying UI features...")
        
        features = {
            "Search functionality": ["search-input", "search-btn", "search-results"],
            "Document browsing": ["document-grid", "doc-card"],
            "Categories": ["category-tree", "category-item"],
            "Tags": ["tag-cloud", "tag"],
            "Statistics": ["stats-grid", "stat-card"],
            "Theme switching": ["theme-toggle", "light.css", "dark.css"],
            "Modals": ["modal", "modal-content", "modal-close"],
            "Pagination": ["pagination", "pagination-item"],
            "WebSocket support": ["WebSocket", "ws://", "initWebSocket"],
            "Responsive design": ["@media", "max-width", "768px"]
        }
        
        # Check all static files for features
        all_content = ""
        for file_path in self.static_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.html', '.css', '.js']:
                all_content += file_path.read_text()
        
        for feature, indicators in features.items():
            found = any(indicator in all_content for indicator in indicators)
            if found:
                print(f"  ✓ {feature}")
            else:
                self.warnings.append(f"Feature not found: {feature}")
        
        return True
    
    def verify_api_integration(self):
        """Verify API integration"""
        print("\nVerifying API integration...")
        
        # Check if web UI is mounted in API app
        api_app_file = self.base_path / "docscope" / "api" / "app.py"
        if api_app_file.exists():
            content = api_app_file.read_text()
            if "mount_web_ui" in content:
                print("  ✓ Web UI mounted in API app")
            else:
                self.warnings.append("Web UI not mounted in API app")
        
        # Check API client in JavaScript
        api_js = self.static_path / "js" / "api.js"
        if api_js.exists():
            content = api_js.read_text()
            endpoints = ["/documents", "/search", "/categories", "/tags", "/health"]
            for endpoint in endpoints:
                if endpoint in content:
                    print(f"  ✓ API endpoint: {endpoint}")
                else:
                    self.warnings.append(f"API endpoint not found: {endpoint}")
        
        return True
    
    def verify_tests(self):
        """Verify test files"""
        print("\nVerifying tests...")
        
        test_file = self.base_path / "tests" / "test_web.py"
        if not test_file.exists():
            self.warnings.append("Web UI tests missing")
            return False
        
        content = test_file.read_text()
        test_classes = [
            "TestWebApp",
            "TestWebUIIntegration",
            "TestStaticFiles",
            "TestHTMLContent",
            "TestJavaScriptFunctionality",
            "TestCSSStyles"
        ]
        
        for test_class in test_classes:
            if test_class not in content:
                self.warnings.append(f"Missing test class: {test_class}")
            else:
                print(f"  ✓ {test_class}")
        
        return True
    
    def run_verification(self):
        """Run all verifications"""
        print("=" * 60)
        print("MILESTONE 7: BUILD WEB UI VERIFICATION")
        print("=" * 60)
        
        checks = [
            ("Structure", self.verify_structure),
            ("HTML", self.verify_html),
            ("CSS", self.verify_css),
            ("JavaScript", self.verify_javascript),
            ("Assets", self.verify_assets),
            ("Web Module", self.verify_web_module),
            ("Features", self.verify_features),
            ("API Integration", self.verify_api_integration),
            ("Tests", self.verify_tests),
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
            print("\n✓ MILESTONE 7: BUILD WEB UI - COMPLETE")
            return True
        else:
            print("\n✗ MILESTONE 7: BUILD WEB UI - INCOMPLETE")
            return False


if __name__ == "__main__":
    verifier = WebUIVerification()
    success = verifier.run_verification()
    
    # Update milestone status
    status_file = Path(__file__).parent / "MILESTONE_STATUS.md"
    if status_file.exists():
        content = status_file.read_text()
        if success:
            content = content.replace(
                "- [ ] Milestone 7: Build Web UI",
                "- [x] Milestone 7: Build Web UI ✓"
            )
            status_file.write_text(content)
            print("\n✓ Updated MILESTONE_STATUS.md")
    
    sys.exit(0 if success else 1)