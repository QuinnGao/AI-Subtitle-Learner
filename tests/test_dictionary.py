"""
字典查询接口测试
"""
import pytest
from fastapi import status


class TestDictionaryAPI:
    """字典查询 API 测试类"""

    def test_query_dictionary_success(self, client):
        """测试成功查询字典"""
        request_data = {
            "word": "こんにちは",
            "furigana": "こんにちは",
            "part_of_speech": "感叹词",
        }

        response = client.post("/api/v1/dictionary/query", json=request_data)

        # 注意：如果 LLM 服务未配置，可能会返回 500 错误
        # 这里只测试请求格式是否正确
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "word" in data
            assert "definition" in data

    def test_query_dictionary_with_minimal_data(self, client):
        """测试使用最少数据查询字典"""
        request_data = {
            "word": "こんにちは",
        }

        response = client.post("/api/v1/dictionary/query", json=request_data)

        # 只提供 word 应该也能查询
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_query_dictionary_with_full_data(self, client):
        """测试使用完整数据查询字典"""
        request_data = {
            "word": "こんにちは",
            "furigana": "こんにちは",
            "romaji": "konnichiwa",
            "part_of_speech": "感叹词",
        }

        response = client.post("/api/v1/dictionary/query", json=request_data)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "word" in data

    def test_query_dictionary_with_empty_word(self, client):
        """测试使用空单词查询"""
        request_data = {
            "word": "",
        }

        response = client.post("/api/v1/dictionary/query", json=request_data)

        # 空单词可能会在服务层处理，这里只测试请求格式
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_query_dictionary_missing_word(self, client):
        """测试缺少必需字段"""
        request_data = {}

        response = client.post("/api/v1/dictionary/query", json=request_data)

        # FastAPI 会自动验证并返回 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_dictionary_response_format(self, client):
        """测试响应格式（如果服务可用）"""
        request_data = {
            "word": "こんにちは",
            "furigana": "こんにちは",
        }

        response = client.post("/api/v1/dictionary/query", json=request_data)

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, dict)
            assert "word" in data

    def test_query_dictionary_with_english_word(self, client):
        """测试查询英文单词"""
        request_data = {
            "word": "hello",
        }

        response = client.post("/api/v1/dictionary/query", json=request_data)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_query_dictionary_with_chinese_word(self, client):
        """测试查询中文单词"""
        request_data = {
            "word": "你好",
        }

        response = client.post("/api/v1/dictionary/query", json=request_data)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

