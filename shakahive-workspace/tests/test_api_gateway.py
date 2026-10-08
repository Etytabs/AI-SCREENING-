"""
Test suite for API Gateway
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.api_gateway.main import app


client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "gateway" in response.json()


def test_submit_application():
    """Test application submission"""
    application_data = {
        "title": "Test Application",
        "abstract": "This is a test abstract",
        "full_proposal": "This is a test proposal",
        "author_name": "Test Author",
        "institution": "Test Institution",
        "email": "test@example.com",
        "budget_amount": 100000,
        "research_area": "Computer Science",
        "keywords": ["AI", "ML"],
        "grant_type": "research",
        "funding_program": "Test Program",
        "project_duration_months": 12
    }
    
    response = client.post("/applications", json=application_data)
    assert response.status_code == 200
    assert "application_id" in response.json()


def test_list_applications():
    """Test listing applications"""
    response = client.get("/applications")
    assert response.status_code == 200
    assert "applications" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
