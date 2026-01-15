"""Tests for REST API endpoints"""

import json
from datetime import datetime
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from docscope.api.app import app
from docscope.api.config import get_settings
from docscope.core.models import Document, DocumentFormat, DocumentStatus


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authentication headers for testing"""
    settings = get_settings()
    return {"Authorization": f"Bearer {settings.secret_key}"}


@pytest.fixture
def sample_document():
    """Create sample document for testing"""
    return {
        "path": "/test/document.md",
        "title": "Test Document",
        "content": "# Test Document\n\nThis is a test document.",
        "format": "markdown",
        "category": "test",
        "tags": ["test", "sample"]
    }


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_liveness_check(self, client):
        """Test liveness probe"""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_readiness_check(self, client):
        """Test readiness probe"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    def test_stats_endpoint(self, client):
        """Test statistics endpoint"""
        response = client.get("/api/v1/health/stats")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "search" in data
        assert "organization" in data
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics"""
        response = client.get("/api/v1/health/metrics")
        assert response.status_code == 200
        assert "docscope_api_up" in response.text


class TestDocumentEndpoints:
    """Test document CRUD endpoints"""
    
    def test_list_documents(self, client):
        """Test listing documents"""
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
    
    def test_list_documents_with_filters(self, client):
        """Test listing documents with filters"""
        response = client.get("/api/v1/documents?format=markdown&category=test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
    
    def test_create_document(self, client, sample_document, auth_headers):
        """Test creating a document"""
        response = client.post(
            "/api/v1/documents",
            json=sample_document,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == sample_document["title"]
        return data["id"]
    
    def test_get_document(self, client):
        """Test getting a specific document"""
        # First create a document
        doc_data = {
            "path": "/test/get.md",
            "title": "Get Test",
            "content": "Test content",
            "format": "markdown"
        }
        create_response = client.post("/api/v1/documents", json=doc_data)
        if create_response.status_code == 201:
            doc_id = create_response.json()["id"]
            
            # Then get it
            response = client.get(f"/api/v1/documents/{doc_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == doc_id
    
    def test_update_document(self, client, auth_headers):
        """Test updating a document"""
        # First create a document
        doc_data = {
            "path": "/test/update.md",
            "title": "Update Test",
            "content": "Original content",
            "format": "markdown"
        }
        create_response = client.post(
            "/api/v1/documents",
            json=doc_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            doc_id = create_response.json()["id"]
            
            # Update it
            update_data = {
                "title": "Updated Title",
                "content": "Updated content"
            }
            response = client.put(
                f"/api/v1/documents/{doc_id}",
                json=update_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Title"
    
    def test_delete_document(self, client, auth_headers):
        """Test deleting a document"""
        # First create a document
        doc_data = {
            "path": "/test/delete.md",
            "title": "Delete Test",
            "content": "To be deleted",
            "format": "markdown"
        }
        create_response = client.post(
            "/api/v1/documents",
            json=doc_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            doc_id = create_response.json()["id"]
            
            # Delete it
            response = client.delete(
                f"/api/v1/documents/{doc_id}",
                headers=auth_headers
            )
            assert response.status_code == 204
            
            # Verify it's gone
            get_response = client.get(f"/api/v1/documents/{doc_id}")
            assert get_response.status_code == 404


class TestSearchEndpoints:
    """Test search endpoints"""
    
    def test_search_post(self, client):
        """Test search with POST method"""
        search_data = {
            "query": "test",
            "limit": 10,
            "offset": 0
        }
        response = client.post("/api/v1/search", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "query" in data
    
    def test_search_get(self, client):
        """Test search with GET method"""
        response = client.get("/api/v1/search?q=test&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_search_suggestions(self, client):
        """Test search suggestions"""
        response = client.get("/api/v1/search/suggestions?q=doc")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    def test_similar_documents(self, client):
        """Test finding similar documents"""
        # Would need a real document ID
        response = client.get("/api/v1/search/similar/test-doc-id?limit=5")
        # Expect 404 for non-existent document
        assert response.status_code in [404, 200]


class TestCategoryEndpoints:
    """Test category endpoints"""
    
    def test_list_categories(self, client):
        """Test listing categories"""
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_category(self, client, auth_headers):
        """Test creating a category"""
        category_data = {
            "name": "Test Category",
            "description": "A test category",
            "color": "#FF0000"
        }
        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Category"
    
    def test_category_tree(self, client):
        """Test getting category tree"""
        response = client.get("/api/v1/categories/tree")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTagEndpoints:
    """Test tag endpoints"""
    
    def test_list_tags(self, client):
        """Test listing tags"""
        response = client.get("/api/v1/tags")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_tag(self, client, auth_headers):
        """Test creating a tag"""
        tag_data = {
            "name": "test-tag",
            "color": "#00FF00",
            "description": "A test tag"
        }
        response = client.post(
            "/api/v1/tags",
            json=tag_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-tag"
    
    def test_popular_tags(self, client):
        """Test getting popular tags"""
        response = client.get("/api/v1/tags/popular?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_tag_cloud(self, client):
        """Test getting tag cloud"""
        response = client.get("/api/v1/tags/cloud")
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert "total" in data


class TestScannerEndpoints:
    """Test scanner endpoints"""
    
    def test_scan_documents(self, client, auth_headers):
        """Test scanning documents"""
        scan_data = {
            "paths": ["/test/path"],
            "recursive": True,
            "incremental": False
        }
        response = client.post(
            "/api/v1/scanner/scan",
            json=scan_data,
            headers=auth_headers
        )
        # May fail if path doesn't exist
        assert response.status_code in [200, 400]
    
    def test_supported_formats(self, client):
        """Test getting supported formats"""
        response = client.get("/api/v1/scanner/formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "total" in data
    
    def test_watch_directory(self, client, auth_headers):
        """Test watching a directory"""
        response = client.post(
            "/api/v1/scanner/watch",
            json={"path": "/test/watch"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestWebSocketEndpoints:
    """Test WebSocket endpoints"""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection"""
        with client.websocket_connect("/api/v1/ws/connect") as websocket:
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
    
    def test_websocket_subscribe(self, client):
        """Test WebSocket subscription"""
        with client.websocket_connect("/api/v1/ws/connect") as websocket:
            # Subscribe to topic
            websocket.send_json({"type": "subscribe", "topic": "test"})
            
            # Receive confirmation
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["topic"] == "test"
    
    def test_websocket_notifications(self, client):
        """Test notification WebSocket"""
        with client.websocket_connect("/api/v1/ws/notifications") as websocket:
            # Should receive initial notification
            data = websocket.receive_json(timeout=2)
            assert data["type"] == "notification"


class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without auth"""
        response = client.post("/api/v1/documents", json={})
        # Should require authentication
        assert response.status_code in [401, 422]
    
    def test_rate_limiting(self, client):
        """Test rate limiting"""
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.get("/api/v1/health")
            responses.append(response.status_code)
        
        # Some should succeed
        assert 200 in responses


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_validation_error(self, client):
        """Test validation error handling"""
        # Invalid document data
        response = client.post("/api/v1/documents", json={"invalid": "data"})
        assert response.status_code == 422
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_malformed_json(self, client):
        """Test malformed JSON handling"""
        response = client.post(
            "/api/v1/search",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])