"""词典查询服务"""

import json
from typing import Dict, Optional

import json_repair

from app.core.llm import call_llm, get_health_checker
from app.core.prompts import get_prompt
from app.core.utils.logger import setup_logger

logger = setup_logger("dictionary_service")


class DictionaryService:
    """词典查询服务"""

    def __init__(self, model: Optional[str] = None):
        """初始化词典查询服务

        Args:
            model: LLM 模型名称，如果为 None 则从健康检查器获取
        """
        self.model = model
        self.health_checker = get_health_checker()

    def query_word(
        self,
        word: str,
        furigana: Optional[str] = None,
        romaji: Optional[str] = None,
        part_of_speech: Optional[str] = None,
    ) -> Dict:
        """查询单词的词典信息

        Args:
            word: 单词文本
            furigana: 平假名读音（可选）
            romaji: 罗马字读音（可选）
            part_of_speech: 词性（可选）

        Returns:
            词典信息字典，包含 word, pronunciation, part_of_speech, meanings 等字段
        """
        # 确保 LLM 配置健康
        self.health_checker.ensure_healthy()

        # 获取模型名称
        if not self.model:
            config = self.health_checker.get_health_status()
            if not config or not config.is_healthy:
                raise ValueError("LLM 配置不健康，无法查询词典")
            self.model = config.model

        # 构建查询信息
        word_info = {
            "text": word,
        }
        if furigana:
            word_info["furigana"] = furigana
        if romaji:
            word_info["romaji"] = romaji
        if part_of_speech:
            word_info["type"] = part_of_speech

        # 加载 prompt
        prompt = get_prompt("dictionary/query")

        # 构建消息
        user_message = f"""请查询以下日语单词的词典信息：

```json
{json.dumps(word_info, ensure_ascii=False, indent=2)}
```

请按照 prompt 要求返回 JSON 格式的词典信息。"""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            # 调用 LLM
            response = call_llm(
                messages=messages,
                model=self.model,
                temperature=0.3,  # 使用较低的温度以获得更准确的结果
            )

            # 提取响应内容
            content = response.choices[0].message.content.strip()

            # 尝试解析 JSON
            try:
                # 先尝试直接解析
                result = json.loads(content)
            except json.JSONDecodeError:
                # 如果失败，尝试修复 JSON
                logger.warning(f"JSON 解析失败，尝试修复: {content[:100]}")
                repaired = json_repair.repair_json(content)
                result = json.loads(repaired)

            logger.info(f"成功查询单词: {word}")
            return result

        except Exception as e:
            logger.error(f"查询单词失败: {word}, error: {str(e)}", exc_info=True)
            # 返回错误信息
            return {
                "word": word,
                "pronunciation": {
                    "furigana": furigana or "",
                    "romaji": romaji or "",
                },
                "part_of_speech": part_of_speech or "未知",
                "meanings": [],
                "error": str(e),
            }
