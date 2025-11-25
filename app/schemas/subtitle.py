"""
字幕处理相关数据模型
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.core.translate.types import TargetLanguage
from app.schemas.common import TaskResponse


def _get_default_max_word_count_cjk() -> int:
    """获取 CJK 最大字数的默认值"""
    try:
        from app.config import settings

        return settings.max_word_count_cjk
    except (ImportError, AttributeError):
        # 如果配置不可用，使用 core/entities.py 中的默认值
        return 25


def _get_default_max_word_count_english() -> int:
    """获取英文最大字数的默认值"""
    try:
        from app.config import settings

        return settings.max_word_count_english
    except (ImportError, AttributeError):
        # 如果配置不可用，使用 core/entities.py 中的默认值
        return 20


class TranslatorService(str, Enum):
    """翻译器服务

    目前仅支持 LLM (OPENAI) 翻译服务。
    TODO: 后续添加其他翻译服务支持（Bing、Google 等）
    """

    OPENAI = "openai"
    # TODO: 后续添加其他翻译服务支持
    # BING = "bing"
    # GOOGLE = "google"


class SubtitleLayout(str, Enum):
    """字幕布局"""

    TRANSLATE_ON_TOP = "translate_on_top"
    ORIGINAL_ON_TOP = "original_on_top"
    ONLY_ORIGINAL = "only_original"
    ONLY_TRANSLATE = "only_translate"


class SubtitleConfig(BaseModel):
    """字幕处理配置"""

    # 翻译配置
    base_url: Optional[str] = Field(None, description="LLM API Base URL")
    api_key: Optional[str] = Field(None, description="LLM API Key")
    llm_model: Optional[str] = Field(None, description="LLM 模型")

    # 翻译服务
    translator_service: Optional[TranslatorService] = Field(
        default=TranslatorService.OPENAI, description="翻译服务"
    )
    need_translate: bool = Field(default=False, description="是否需要翻译")
    need_optimize: bool = Field(default=False, description="是否需要优化")
    need_reflect: bool = Field(default=False, description="是否需要反思翻译")
    need_analyze_japanese: bool = Field(
        default=True, description="是否需要分析日语文本（提取平假名、罗马字、词性）"
    )
    thread_num: int = Field(default=10, ge=1, description="并发线程数")
    batch_size: int = Field(default=10, ge=1, description="批处理大小")

    # 字幕布局和分割
    subtitle_layout: SubtitleLayout = Field(
        default=SubtitleLayout.ORIGINAL_ON_TOP, description="字幕布局"
    )
    max_word_count_cjk: int = Field(
        default_factory=_get_default_max_word_count_cjk,
        ge=1,
        description="CJK 语言最大字数",
    )
    max_word_count_english: int = Field(
        default_factory=_get_default_max_word_count_english,
        ge=1,
        description="英文最大字数",
    )
    need_split: bool = Field(default=True, description="是否需要分割")
    target_language: Optional[TargetLanguage] = Field(
        default=TargetLanguage.SIMPLIFIED_CHINESE, description="目标语言"
    )
    subtitle_style: Optional[str] = Field(None, description="字幕样式")
    custom_prompt_text: Optional[str] = Field(None, description="自定义提示词")


class SubtitleRequest(BaseModel):
    """字幕处理请求

    注意：subtitle_path 和 video_path 已移除，现在统一从数据库获取文件路径
    """

    output_path: Optional[str] = Field(
        None, description="输出文件路径（可选，MinIO 路径）"
    )
    config: SubtitleConfig = Field(
        default_factory=SubtitleConfig, description="字幕处理配置"
    )


class TranscribeTaskInfo(BaseModel):
    """转录任务信息"""

    task_id: Optional[str] = Field(None, description="转录任务ID")
    status: Optional[str] = Field(None, description="转录任务状态")
    progress: Optional[int] = Field(None, description="转录任务进度")
    message: Optional[str] = Field(None, description="转录任务消息")


class VideoTaskInfo(BaseModel):
    """视频下载任务信息"""

    task_id: Optional[str] = Field(None, description="视频下载任务ID")
    status: Optional[str] = Field(None, description="视频下载任务状态")
    progress: Optional[int] = Field(None, description="视频下载任务进度")
    message: Optional[str] = Field(None, description="视频下载任务消息")


class SubtitleResponse(TaskResponse):
    """字幕处理响应"""

    transcribe_task: Optional[TranscribeTaskInfo] = Field(
        None, description="关联的转录任务信息"
    )
    video_task: Optional[VideoTaskInfo] = Field(
        None, description="关联的视频下载任务信息"
    )


class DictionaryQueryRequest(BaseModel):
    """词典查询请求"""

    word: str = Field(..., description="单词文本")
    furigana: Optional[str] = Field(None, description="平假名读音")
    romaji: Optional[str] = Field(None, description="罗马字读音")
    part_of_speech: Optional[str] = Field(None, description="词性")


class DictionaryMeaning(BaseModel):
    """词典释义"""

    meaning: str = Field(..., description="中文释义")
    example: Optional[str] = Field(None, description="例句（日语）")
    example_translation: Optional[str] = Field(None, description="例句翻译（中文）")


class DictionaryPronunciation(BaseModel):
    """词典发音信息"""

    furigana: str = Field(default="", description="平假名读音")
    romaji: str = Field(default="", description="罗马字读音")


class DictionaryQueryResponse(BaseModel):
    """词典查询响应"""

    word: str = Field(..., description="单词文本")
    pronunciation: DictionaryPronunciation = Field(..., description="发音信息")
    part_of_speech: str = Field(..., description="词性（中文）")
    meanings: list[DictionaryMeaning] = Field(
        default_factory=list, description="释义列表"
    )
    usage_notes: Optional[str] = Field(None, description="使用说明")
    error: Optional[str] = Field(None, description="错误信息（如果有）")
