# coding:utf-8
"""
配置模块

此模块提供配置的默认值，用于兼容需要配置的代码。
在 FastAPI 环境中，实际配置应通过 app.config.Settings 管理。
"""

from enum import Enum
from pathlib import Path

from app.config import settings
from app.core.entities import (
    LLMServiceEnum,
    SubtitleLayoutEnum,
    TranscribeLanguageEnum,
    TranscribeModelEnum,
    TranscribeOutputFormatEnum,
    TranslatorServiceEnum,
    VideoQualityEnum,
)
from app.core.translate.types import TargetLanguage


class ConfigItem:
    """配置项"""

    def __init__(self, section: str, key: str, default_value, validator=None):
        self.section = section
        self.key = key
        self._value = default_value
        self.validator = validator

    @property
    def value(self):
        """获取配置值"""
        return self._value

    @value.setter
    def value(self, val):
        """设置配置值"""
        if self.validator:
            if hasattr(self.validator, "validate"):
                if not self.validator.validate(val):
                    val = (
                        self.validator.correct(val)
                        if hasattr(self.validator, "correct")
                        else self._value
                    )
        self._value = val


class OptionsConfigItem(ConfigItem):
    """选项配置项"""

    def __init__(
        self, section: str, key: str, default_value, validator=None, serializer=None
    ):
        super().__init__(section, key, default_value, validator)
        self.serializer = serializer


class RangeConfigItem(ConfigItem):
    """范围配置项"""

    def __init__(self, section: str, key: str, default_value, validator=None):
        super().__init__(section, key, default_value, validator)


class Config:
    """应用配置（FastAPI 环境版本）"""

    # LLM配置
    llm_service = OptionsConfigItem("LLM", "LLMService", LLMServiceEnum.OPENAI)

    openai_model = ConfigItem("LLM", "OpenAI_Model", "gpt-4o-mini")
    openai_api_key = ConfigItem("LLM", "OpenAI_API_Key", "")
    openai_api_base = ConfigItem("LLM", "OpenAI_API_Base", "https://api.openai.com/v1")

    silicon_cloud_model = ConfigItem("LLM", "SiliconCloud_Model", "gpt-4o-mini")
    silicon_cloud_api_key = ConfigItem("LLM", "SiliconCloud_API_Key", "")
    silicon_cloud_api_base = ConfigItem(
        "LLM", "SiliconCloud_API_Base", "https://api.siliconflow.cn/v1"
    )

    deepseek_model = ConfigItem("LLM", "DeepSeek_Model", "deepseek-chat")
    deepseek_api_key = ConfigItem("LLM", "DeepSeek_API_Key", "")
    deepseek_api_base = ConfigItem(
        "LLM", "DeepSeek_API_Base", "https://api.deepseek.com/v1"
    )

    ollama_model = ConfigItem("LLM", "Ollama_Model", "llama2")
    ollama_api_key = ConfigItem("LLM", "Ollama_API_Key", "ollama")
    ollama_api_base = ConfigItem("LLM", "Ollama_API_Base", "http://localhost:11434/v1")

    lm_studio_model = ConfigItem("LLM", "LmStudio_Model", "qwen2.5:7b")
    lm_studio_api_key = ConfigItem("LLM", "LmStudio_API_Key", "lmstudio")
    lm_studio_api_base = ConfigItem(
        "LLM", "LmStudio_API_Base", "http://localhost:1234/v1"
    )

    gemini_model = ConfigItem("LLM", "Gemini_Model", "gemini-pro")
    gemini_api_key = ConfigItem("LLM", "Gemini_API_Key", "")
    gemini_api_base = ConfigItem(
        "LLM",
        "Gemini_API_Base",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    chatglm_model = ConfigItem("LLM", "ChatGLM_Model", "glm-4")
    chatglm_api_key = ConfigItem("LLM", "ChatGLM_API_Key", "")
    chatglm_api_base = ConfigItem(
        "LLM", "ChatGLM_API_Base", "https://open.bigmodel.cn/api/paas/v4"
    )

    # ------------------- 翻译配置 -------------------
    # TODO: 目前仅支持 LLM (OPENAI) 翻译服务，后续添加其他翻译服务支持
    translator_service = OptionsConfigItem(
        "Translate",
        "TranslatorServiceEnum",
        TranslatorServiceEnum.OPENAI,
    )
    need_reflect_translate = ConfigItem("Translate", "NeedReflectTranslate", False)
    batch_size = RangeConfigItem("Translate", "BatchSize", 5)
    thread_num = RangeConfigItem("Translate", "ThreadNum", 8)

    # ------------------- 转录配置 -------------------
    transcribe_model = OptionsConfigItem(
        "Transcribe",
        "TranscribeModel",
        TranscribeModelEnum.WHISPERX,
    )
    transcribe_output_format = OptionsConfigItem(
        "Transcribe",
        "OutputFormat",
        TranscribeOutputFormatEnum.SRT,
    )
    transcribe_language = OptionsConfigItem(
        "Transcribe",
        "TranscribeLanguage",
        TranscribeLanguageEnum.ENGLISH,
    )

    # ------------------- 字幕配置 -------------------
    need_optimize = ConfigItem("Subtitle", "NeedOptimize", False)
    need_translate = ConfigItem("Subtitle", "NeedTranslate", False)
    need_split = ConfigItem("Subtitle", "NeedSplit", False)
    target_language = OptionsConfigItem(
        "Subtitle",
        "TargetLanguage",
        TargetLanguage.SIMPLIFIED_CHINESE,
    )
    max_word_count_cjk = ConfigItem("Subtitle", "MaxWordCountCJK", 25)
    max_word_count_english = ConfigItem("Subtitle", "MaxWordCountEnglish", 20)
    custom_prompt_text = ConfigItem("Subtitle", "CustomPromptText", "")

    # ------------------- 字幕合成配置 -------------------
    soft_subtitle = ConfigItem("Video", "SoftSubtitle", False)
    need_video = ConfigItem("Video", "NeedVideo", True)
    video_quality = OptionsConfigItem(
        "Video",
        "VideoQuality",
        VideoQualityEnum.MEDIUM,
    )

    # ------------------- 字幕样式配置 -------------------
    subtitle_style_name = ConfigItem("SubtitleStyle", "StyleName", "default")
    subtitle_layout = OptionsConfigItem(
        "SubtitleStyle",
        "Layout",
        SubtitleLayoutEnum.TRANSLATE_ON_TOP,
    )
    subtitle_preview_image = ConfigItem("SubtitleStyle", "PreviewImage", "")

    # ------------------- 保存配置 -------------------
    work_dir = ConfigItem(
        "Save", "Work_Dir", getattr(settings, "work_dir", Path("./workspace"))
    )

    # ------------------- 缓存配置 -------------------
    cache_enabled = ConfigItem("Cache", "CacheEnabled", True)


# 创建配置实例
cfg = Config()

# 从 app.config.settings 同步配置值（如果可用）
try:
    cfg.max_word_count_cjk.value = settings.max_word_count_cjk
    cfg.max_word_count_english.value = settings.max_word_count_english
    cfg.work_dir.value = settings.work_dir
except AttributeError:
    pass
