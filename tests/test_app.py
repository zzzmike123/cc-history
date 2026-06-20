"""Tests for app.py Flask API endpoints."""

import pytest
from src.cc_history.app import app


@pytest.fixture
def client():
    """创建测试客户端。"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """健康检查接口测试。"""

    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True


class TestProjectsEndpoint:
    """项目列表接口测试。"""

    def test_projects_returns_list(self, client):
        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


class TestMessagesEndpoint:
    """消息接口测试。"""

    def test_missing_params(self, client):
        response = client.get("/api/messages")
        assert response.status_code == 400

    def test_invalid_session_id(self, client):
        response = client.get("/api/messages?projectDir=/test&sessionId=not-a-uuid")
        assert response.status_code == 400
        data = response.get_json()
        assert "无效" in data["error"]

    def test_path_traversal(self, client):
        response = client.get("/api/messages?projectDir=/etc/passwd&sessionId=550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 400
        data = response.get_json()
        assert "无效" in data["error"]


class TestSearchEndpoint:
    """搜索接口测试。"""

    def test_empty_query(self, client):
        response = client.get("/api/search?q=")
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_search_returns_list(self, client):
        response = client.get("/api/search?q=test")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


class TestSkillsEndpoint:
    """Skills 接口测试。"""

    def test_skills_returns_list(self, client):
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


class TestPluginsEndpoint:
    """插件接口测试。"""

    def test_plugins_returns_list(self, client):
        response = client.get("/api/plugins")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


class TestFavoritesEndpoint:
    """收藏接口测试。"""

    def test_get_favorites(self, client):
        response = client.get("/api/favorites")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

    def test_toggle_favorite_invalid_id(self, client):
        response = client.post("/api/favorites",
                               json={"sessionId": "not-a-uuid"})
        assert response.status_code == 400

    def test_toggle_favorite_missing_id(self, client):
        response = client.post("/api/favorites", json={})
        assert response.status_code == 400


class TestCustomNamesEndpoint:
    """自定义名称接口测试。"""

    def test_get_custom_names(self, client):
        response = client.get("/api/custom-names")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

    def test_set_custom_name_invalid_id(self, client):
        response = client.post("/api/custom-names",
                               json={"sessionId": "not-a-uuid", "name": "test"})
        assert response.status_code == 400


class TestExportEndpoint:
    """导出接口测试。"""

    def test_export_missing_id(self, client):
        response = client.get("/api/export")
        assert response.status_code == 400

    def test_export_invalid_id(self, client):
        response = client.get("/api/export?sessionId=not-a-uuid")
        assert response.status_code == 400


class TestSettingsEndpoint:
    """设置接口测试。"""

    def test_get_settings(self, client):
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.get_json()
        assert "claude_dir" in data
        assert "theme" in data


class TestStatsEndpoint:
    """统计接口测试。"""

    def test_stats(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "totalSessions" in data
        assert "totalMessages" in data
        assert "totalProjects" in data
