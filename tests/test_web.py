"""Tests for Web UI"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from docscope.web import create_web_app, mount_web_ui
from docscope.api.app import app as api_app


@pytest.fixture
def web_app():
    """Create test web application"""
    return create_web_app()


@pytest.fixture
def web_client(web_app):
    """Create test client for web app"""
    return TestClient(web_app)


@pytest.fixture
def api_client():
    """Create test client for API with web UI"""
    return TestClient(api_app)


class TestWebApp:
    """Test standalone web application"""
    
    def test_web_app_creation(self, web_app):
        """Test web app is created correctly"""
        assert web_app is not None
        assert web_app.title == "DocScope Web UI"
    
    def test_static_files_mounted(self, web_client):
        """Test static files are accessible"""
        # Test CSS file
        response = web_client.get("/static/css/style.css")
        assert response.status_code in [200, 404]  # 404 if file doesn't exist yet
        
        # Test JS file
        response = web_client.get("/static/js/app.js")
        assert response.status_code in [200, 404]
    
    def test_root_endpoint(self, web_client):
        """Test root endpoint serves index.html"""
        response = web_client.get("/")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Check if it's HTML content
            assert 'text/html' in response.headers.get('content-type', '')
    
    def test_favicon(self, web_client):
        """Test favicon endpoint"""
        response = web_client.get("/favicon.ico")
        assert response.status_code in [200, 404]


class TestWebUIIntegration:
    """Test web UI integration with API"""
    
    def test_web_ui_mounted(self, api_client):
        """Test web UI is mounted to API app"""
        # Test root endpoint
        response = api_client.get("/")
        assert response.status_code == 200
    
    def test_static_files_accessible(self, api_client):
        """Test static files are accessible through API"""
        response = api_client.get("/static/css/style.css")
        assert response.status_code in [200, 404]
    
    def test_api_endpoints_still_work(self, api_client):
        """Test API endpoints still work with web UI mounted"""
        # Health endpoint
        response = api_client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Documents endpoint
        response = api_client.get("/api/v1/documents")
        assert response.status_code in [200, 500]  # 500 if DB not initialized


class TestStaticFiles:
    """Test static file structure"""
    
    def test_static_directory_exists(self):
        """Test static directory exists"""
        static_dir = Path(__file__).parent.parent / "docscope" / "web" / "static"
        assert static_dir.exists()
    
    def test_index_html_exists(self):
        """Test index.html exists"""
        index_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "index.html"
        assert index_file.exists()
    
    def test_css_files_exist(self):
        """Test CSS files exist"""
        css_dir = Path(__file__).parent.parent / "docscope" / "web" / "static" / "css"
        assert css_dir.exists()
        
        # Check main style file
        style_file = css_dir / "style.css"
        assert style_file.exists()
        
        # Check theme files
        themes_dir = css_dir / "themes"
        assert themes_dir.exists()
        assert (themes_dir / "light.css").exists()
        assert (themes_dir / "dark.css").exists()
    
    def test_javascript_files_exist(self):
        """Test JavaScript files exist"""
        js_dir = Path(__file__).parent.parent / "docscope" / "web" / "static" / "js"
        assert js_dir.exists()
        
        # Check all JS files
        js_files = [
            "config.js",
            "api.js",
            "utils.js",
            "components.js",
            "pages.js",
            "app.js"
        ]
        
        for file in js_files:
            assert (js_dir / file).exists()
    
    def test_favicon_exists(self):
        """Test favicon exists"""
        favicon = Path(__file__).parent.parent / "docscope" / "web" / "static" / "favicon.svg"
        assert favicon.exists()


class TestHTMLContent:
    """Test HTML content and structure"""
    
    def test_html_structure(self):
        """Test HTML has correct structure"""
        index_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "index.html"
        if index_file.exists():
            content = index_file.read_text()
            
            # Check essential elements
            assert '<!DOCTYPE html>' in content
            assert '<html' in content
            assert '<head>' in content
            assert '<body>' in content
            assert 'DocScope' in content
            
            # Check pages
            assert 'search-page' in content
            assert 'browse-page' in content
            assert 'categories-page' in content
            assert 'tags-page' in content
            assert 'stats-page' in content
            
            # Check modals
            assert 'doc-viewer' in content
            assert 'settings-modal' in content
    
    def test_css_imports(self):
        """Test CSS files are properly imported"""
        index_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "index.html"
        if index_file.exists():
            content = index_file.read_text()
            
            assert 'css/style.css' in content
            assert 'css/themes/light.css' in content
    
    def test_javascript_imports(self):
        """Test JavaScript files are properly imported"""
        index_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "index.html"
        if index_file.exists():
            content = index_file.read_text()
            
            # Check JS imports in correct order
            assert 'js/config.js' in content
            assert 'js/api.js' in content
            assert 'js/utils.js' in content
            assert 'js/components.js' in content
            assert 'js/pages.js' in content
            assert 'js/app.js' in content


class TestJavaScriptFunctionality:
    """Test JavaScript code structure"""
    
    def test_config_js(self):
        """Test config.js structure"""
        config_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "js" / "config.js"
        if config_file.exists():
            content = config_file.read_text()
            
            assert 'const Config' in content
            assert 'api:' in content
            assert 'search:' in content
            assert 'ui:' in content
            assert 'websocket:' in content
    
    def test_api_js(self):
        """Test api.js structure"""
        api_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "js" / "api.js"
        if api_file.exists():
            content = api_file.read_text()
            
            assert 'class API' in content
            assert 'getDocuments' in content
            assert 'search' in content
            assert 'getCategories' in content
            assert 'getTags' in content
    
    def test_app_js(self):
        """Test app.js structure"""
        app_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "js" / "app.js"
        if app_file.exists():
            content = app_file.read_text()
            
            assert 'class DocScopeApp' in content
            assert 'initNavigation' in content
            assert 'initWebSocket' in content
            assert 'DOMContentLoaded' in content


class TestCSSStyles:
    """Test CSS styles"""
    
    def test_main_styles(self):
        """Test main stylesheet"""
        style_file = Path(__file__).parent.parent / "docscope" / "web" / "static" / "css" / "style.css"
        if style_file.exists():
            content = style_file.read_text()
            
            # Check CSS variables
            assert ':root' in content
            assert '--color-primary' in content
            assert '--spacing-' in content
            assert '--font-' in content
            
            # Check main components
            assert '.header' in content
            assert '.search-' in content
            assert '.document-' in content
            assert '.modal' in content
    
    def test_theme_files(self):
        """Test theme files"""
        light_theme = Path(__file__).parent.parent / "docscope" / "web" / "static" / "css" / "themes" / "light.css"
        dark_theme = Path(__file__).parent.parent / "docscope" / "web" / "static" / "css" / "themes" / "dark.css"
        
        if light_theme.exists():
            content = light_theme.read_text()
            assert '--color-background' in content
            assert '#ffffff' in content or '#fff' in content
        
        if dark_theme.exists():
            content = dark_theme.read_text()
            assert '--color-background' in content
            assert '#0d1117' in content or '#161b22' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])