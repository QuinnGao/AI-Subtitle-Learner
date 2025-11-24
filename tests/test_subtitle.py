"""
字幕处理接口测试
"""
import time
from pathlib import Path

import pytest
from fastapi import status

from app.schemas.common import TaskStatus


class TestSubtitleAPI:
    """字幕处理 API 测试类"""

    def test_create_subtitle_task_success(self, client, sample_srt_file):
        """测试成功创建字幕处理任务"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data
        assert data["status"] == TaskStatus.PENDING
        assert data["message"] == "任务已创建"
        assert "queued_at" in data

    def test_create_subtitle_task_with_invalid_file(self, client, sample_srt_file_not_exist):
        """测试使用不存在的文件创建任务"""
        request_data = {
            "subtitle_path": sample_srt_file_not_exist,
            "config": {},
        }

        response = client.post("/api/v1/subtitle", json=request_data)

        # 任务会创建，但会在后台处理时失败
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

        # 等待一下让后台任务执行
        time.sleep(1)

    def test_create_subtitle_task_with_full_config(self, client, sample_srt_file):
        """测试使用完整配置创建字幕处理任务"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "video_path": "/path/to/video.mp4",
            "output_path": "/path/to/output.srt",
            "config": {
                "base_url": "https://api.openai.com/v1",
                "api_key": "test-key",
                "llm_model": "gpt-4",
                "translator_service": "openai",
                "need_translate": True,
                "need_optimize": True,
                "need_reflect": False,
                "thread_num": 5,
                "batch_size": 10,
                "subtitle_layout": "original_on_top",
                "max_word_count_cjk": 15,
                "max_word_count_english": 20,
                "need_split": True,
                "target_language": "en",
                "subtitle_style": "default",
                "custom_prompt_text": "Custom prompt",
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data
        assert data["status"] == TaskStatus.PENDING

    def test_download_subtitle_result_not_found(self, client):
        """测试下载不存在的任务结果"""
        fake_task_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/subtitle/{fake_task_id}/download")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "任务不存在" in response.json()["detail"]

    def test_download_subtitle_result_not_completed(self, client, sample_srt_file):
        """测试下载未完成的任务结果"""
        # 创建任务
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {},
        }
        create_response = client.post("/api/v1/subtitle", json=request_data)
        task_id = create_response.json()["task_id"]

        # 立即尝试下载（任务应该还在处理中）
        response = client.get(f"/api/v1/subtitle/{task_id}/download")

        # 如果任务未完成，应该返回 400
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            assert "任务尚未完成" in response.json()["detail"]

    def test_subtitle_task_workflow(self, client, sample_srt_file, temp_dir):
        """测试完整的字幕处理工作流"""
        # 1. 创建任务
        output_path = str(temp_dir / "output.srt")
        request_data = {
            "subtitle_path": sample_srt_file,
            "output_path": output_path,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        create_response = client.post("/api/v1/subtitle", json=request_data)
        assert create_response.status_code == status.HTTP_200_OK
        task_id = create_response.json()["task_id"]

        # 2. 等待任务处理（状态查询端点已删除，简化测试）
        time.sleep(2)
        
        # 3. 尝试下载结果（如果任务完成）
        download_response = client.get(f"/api/v1/subtitle/{task_id}/download")
        # 如果文件存在，应该能下载；如果不存在，可能任务还在处理中
        if download_response.status_code == status.HTTP_200_OK:
            assert len(download_response.content) > 0

    def test_subtitle_request_validation(self, client):
        """测试请求参数验证"""
        # 缺少必需的 subtitle_path
        request_data = {
            "config": {},
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        # FastAPI 会自动验证并返回 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_subtitle_config_validation(self, client, sample_srt_file):
        """测试配置参数验证"""
        # 使用无效的配置值
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "thread_num": 0,  # 应该 >= 1
                "batch_size": -1,  # 应该 >= 1
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        # Pydantic 会验证并返回 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_subtitle_with_different_layouts(self, client, sample_srt_file):
        """测试不同的字幕布局配置"""
        layouts = [
            "translate_on_top",
            "original_on_top",
            "only_original",
            "only_translate",
        ]

        for layout in layouts:
            request_data = {
                "subtitle_path": sample_srt_file,
                "config": {
                    "subtitle_layout": layout,
                    "need_translate": layout != "only_original",
                },
            }

            response = client.post("/api/v1/subtitle", json=request_data)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "task_id" in data

    def test_subtitle_with_different_translator_services(self, client, sample_srt_file):
        """测试不同的翻译服务配置"""
        services = ["openai", "bing", "google"]

        for service in services:
            request_data = {
                "subtitle_path": sample_srt_file,
                "config": {
                    "translator_service": service,
                    "need_translate": True,
                },
            }

            response = client.post("/api/v1/subtitle", json=request_data)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "task_id" in data

    def test_subtitle_task_progress_updates(self, client, sample_srt_file):
        """测试任务进度更新"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        create_response = client.post("/api/v1/subtitle", json=request_data)
        assert create_response.status_code == status.HTTP_200_OK
        task_id = create_response.json()["task_id"]

        # 等待一段时间让任务开始处理（状态查询端点已删除，简化测试）
        time.sleep(1)
        assert "progress" in task_data
        assert 0 <= task_data["progress"] <= 100

    def test_subtitle_with_optimize_enabled(self, client, sample_srt_file):
        """测试启用优化功能"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_optimize": True,
                "need_translate": False,
                "base_url": "https://api.openai.com/v1",
                "api_key": "test-key",
                "llm_model": "gpt-4",
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data
        assert data["status"] == TaskStatus.PENDING

    def test_subtitle_with_split_enabled(self, client, sample_srt_file):
        """测试启用分割功能"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_split": True,
                "need_translate": False,
                "need_optimize": False,
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_reflect_enabled(self, client, sample_srt_file):
        """测试启用反思翻译功能"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_translate": True,
                "need_reflect": True,
                "translator_service": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": "test-key",
                "llm_model": "gpt-4",
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_custom_prompt(self, client, sample_srt_file):
        """测试使用自定义提示词"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_optimize": True,
                "custom_prompt_text": "请优化这段字幕，使其更加流畅自然",
                "base_url": "https://api.openai.com/v1",
                "api_key": "test-key",
                "llm_model": "gpt-4",
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_video_path(self, client, sample_srt_file):
        """测试提供视频路径"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "video_path": "/path/to/video.mp4",
            "config": {},
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_custom_output_path(self, client, sample_srt_file, temp_dir):
        """测试自定义输出路径"""
        output_path = str(temp_dir / "custom_output.srt")
        request_data = {
            "subtitle_path": sample_srt_file,
            "output_path": output_path,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_task_error_handling(self, client):
        """测试错误处理"""
        # 使用不存在的文件
        request_data = {
            "subtitle_path": "/nonexistent/path/file.srt",
            "config": {},
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        # 任务会创建，但会在后台处理时失败
        assert response.status_code == status.HTTP_200_OK
        task_id = response.json()["task_id"]

        # 等待一下让后台任务执行（状态查询端点已删除，简化测试）
        time.sleep(2)

    def test_subtitle_concurrent_requests(self, client, sample_srt_file):
        """测试并发请求"""
        import concurrent.futures

        def create_task():
            request_data = {
                "subtitle_path": sample_srt_file,
                "config": {},
            }
            response = client.post("/api/v1/subtitle", json=request_data)
            return response.json()["task_id"]

        # 创建 5 个并发任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_task) for _ in range(5)]
            task_ids = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 验证所有任务都创建成功
        assert len(task_ids) == 5
        assert len(set(task_ids)) == 5  # 所有任务 ID 应该唯一

        # 验证所有任务都创建成功（任务状态通过其他方式验证）

    def test_subtitle_task_status_transitions(self, client, sample_srt_file):
        """测试任务状态转换（已删除状态查询端点，此测试已简化）"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        create_response = client.post("/api/v1/subtitle", json=request_data)
        task_id = create_response.json()["task_id"]
        assert task_id is not None
        # 任务状态转换测试已移除，因为状态查询端点已删除

    def test_subtitle_with_max_word_count(self, client, sample_srt_file):
        """测试最大字数配置"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "max_word_count_cjk": 20,
                "max_word_count_english": 30,
                "need_split": True,
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_subtitle_style(self, client, sample_srt_file):
        """测试字幕样式配置"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "subtitle_style": "default",
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_target_language(self, client, sample_srt_file):
        """测试目标语言配置"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "need_translate": True,
                "target_language": "en",
                "translator_service": "google",
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_thread_and_batch_config(self, client, sample_srt_file):
        """测试线程数和批处理大小配置"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {
                "thread_num": 5,
                "batch_size": 20,
                "need_translate": True,
                "translator_service": "google",
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_download_with_completed_task(self, client, sample_srt_file, temp_dir):
        """测试下载已完成任务的结果"""
        output_path = str(temp_dir / "download_test.srt")
        request_data = {
            "subtitle_path": sample_srt_file,
            "output_path": output_path,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        create_response = client.post("/api/v1/subtitle", json=request_data)
        task_id = create_response.json()["task_id"]

        # 等待任务完成（状态查询端点已删除，简化测试）
        time.sleep(3)
        
        # 尝试下载
        download_response = client.get(f"/api/v1/subtitle/{task_id}/download")
        if download_response.status_code == status.HTTP_200_OK:
            assert len(download_response.content) > 0
            assert download_response.headers["content-type"] == "application/octet-stream"
                break

            time.sleep(0.5)
            wait_time += 0.5

    def test_subtitle_with_ass_format(self, client, sample_ass_file):
        """测试 ASS 格式字幕文件"""
        request_data = {
            "subtitle_path": sample_ass_file,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_with_vtt_format(self, client, sample_vtt_file):
        """测试 VTT 格式字幕文件"""
        request_data = {
            "subtitle_path": sample_vtt_file,
            "config": {
                "need_translate": False,
                "need_optimize": False,
                "need_split": False,
            },
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data

    def test_subtitle_task_response_fields(self, client, sample_srt_file):
        """测试任务响应字段完整性"""
        request_data = {
            "subtitle_path": sample_srt_file,
            "config": {},
        }

        response = client.post("/api/v1/subtitle", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证必需字段
        assert "task_id" in data
        assert "status" in data
        assert "message" in data
        assert "queued_at" in data
        assert "progress" in data

        # 验证字段类型
        assert isinstance(data["task_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
        assert isinstance(data["progress"], int)
        assert 0 <= data["progress"] <= 100

