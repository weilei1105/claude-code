"""Tests for API endpoints."""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestReportTypesEndpoint:
    """Tests for report types endpoint."""

    def test_get_report_types(self, client):
        """Test getting available report types."""
        response = client.get("/api/report-types")
        assert response.status_code == 200
        data = response.json()
        assert "report_types" in data
        report_types = data["report_types"]
        assert "trend" in report_types
        assert "compare" in report_types
        assert "comprehensive" in report_types
        assert "policy" in report_types


class TestGenerateEndpoint:
    """Tests for report generation endpoint."""

    def test_generate_invalid_report_type(self, client):
        """Test generating report with invalid type returns error."""
        response = client.post(
            "/api/generate",
            json={
                "topic": "测试主题",
                "report_type": "invalid_type",
                "report_depth": "simple",
            },
        )
        # FastAPI returns 422 for validation errors including invalid enums
        assert response.status_code == 422

    def test_generate_missing_topic(self, client):
        """Test generating report without topic returns validation error."""
        response = client.post(
            "/api/generate",
            json={
                "report_type": "trend",
                "report_depth": "simple",
            },
        )
        assert response.status_code == 422  # Validation error

    def test_generate_empty_topic(self, client):
        """Test generating report with empty topic returns validation error."""
        response = client.post(
            "/api/generate",
            json={
                "topic": "",
                "report_type": "trend",
                "report_depth": "simple",
            },
        )
        assert response.status_code == 422  # Validation error


class TestStatusEndpoint:
    """Tests for task status endpoint."""

    def test_status_nonexistent_task(self, client):
        """Test getting status of non-existent task returns 404."""
        response = client.get("/api/status/nonexistent123")
        assert response.status_code == 404


class TestStopEndpoint:
    """Tests for stop task endpoint."""

    def test_stop_nonexistent_task(self, client):
        """Test stopping non-existent task returns 404."""
        response = client.post("/api/stop/nonexistent123")
        assert response.status_code == 404


class TestReportsEndpoint:
    """Tests for reports listing endpoint."""

    def test_list_reports(self, client):
        """Test listing generated reports."""
        response = client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert isinstance(data["reports"], list)


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
