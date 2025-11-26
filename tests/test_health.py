"""
健康检查接口测试
"""
import pytest
from fastapi import status


class TestHealthAPI:
    """健康检查 API 测试类"""

    def test_health_check_success(self, client):
        """测试健康检查成功"""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_response_format(self, client):
        """测试健康检查响应格式"""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert isinstance(data["status"], str)

