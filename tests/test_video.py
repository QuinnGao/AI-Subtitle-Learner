"""
视频分析接口测试
"""
import time

import pytest
from fastapi import status

from app.core.constants import TaskStatus


class TestVideoAPI:
    """视频分析 API 测试类"""

    def test_start_analysis_with_url(self, client):
        """测试通过 URL 开始分析任务"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = client.post(f"/api/v1/video/analyze?url={url}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data
        assert data["status"] == TaskStatus.PENDING
        assert "message" in data
        assert isinstance(data["task_id"], str)

    def test_start_analysis_with_invalid_url(self, client):
        """测试使用无效 URL 开始分析任务"""
        url = "not-a-valid-url"
        response = client.post(f"/api/v1/video/analyze?url={url}")

        # 任务会创建，但会在后台处理时失败
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_get_analysis_task_status_not_found(self, client):
        """测试查询不存在的任务状态"""
        fake_task_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/video/analyze/{fake_task_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "任务不存在" in response.json()["detail"]

    def test_get_analysis_task_status_success(self, client):
        """测试查询任务状态成功"""
        # 先创建一个任务
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        create_response = client.post(f"/api/v1/video/analyze?url={url}")
        assert create_response.status_code == status.HTTP_200_OK
        task_id = create_response.json()["task_id"]

        # 查询任务状态
        response = client.get(f"/api/v1/video/analyze/{task_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "task_id" in data
        assert "status" in data
        assert "progress" in data
        assert "message" in data
        assert data["task_id"] == task_id
        assert isinstance(data["progress"], (int, float))
        assert 0 <= data["progress"] <= 100

    def test_analysis_task_response_fields(self, client):
        """测试任务响应字段完整性"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = client.post(f"/api/v1/video/analyze?url={url}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证必需字段
        assert "task_id" in data
        assert "status" in data
        assert "message" in data

        # 验证字段类型
        assert isinstance(data["task_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)

    def test_analysis_task_with_empty_url(self, client):
        """测试使用空 URL"""
        url = ""
        response = client.post(f"/api/v1/video/analyze?url={url}")

        # 空 URL 应该也能创建任务，但会在后台处理时失败
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_analysis_task_concurrent_requests(self, client):
        """测试并发请求"""
        import concurrent.futures

        def create_task():
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            response = client.post(f"/api/v1/video/analyze?url={url}")
            return response.json()["task_id"]

        # 创建 3 个并发任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_task) for _ in range(3)]
            task_ids = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 验证所有任务都创建成功
        assert len(task_ids) == 3
        assert len(set(task_ids)) == 3  # 所有任务 ID 应该唯一

    def test_analysis_task_status_progress(self, client):
        """测试任务进度更新"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        create_response = client.post(f"/api/v1/video/analyze?url={url}")
        task_id = create_response.json()["task_id"]

        # 等待一下让任务开始处理
        time.sleep(1)

        # 查询任务状态
        response = client.get(f"/api/v1/video/analyze/{task_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "progress" in data
        assert isinstance(data["progress"], (int, float))
        assert 0 <= data["progress"] <= 100

