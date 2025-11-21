"""日语文本分析模块

使用LLM分析日语文本，提取每个词的平假名、罗马字和词性。
"""

import asyncio
import json
import re
from typing import Dict, List, Tuple

import json_repair

from ..llm import call_llm
from ..prompts import get_prompt
from ..utils.logger import setup_logger


logger = setup_logger("japanese_analyzer")

MAX_STEPS = 3


class JapaneseAnalyzer:
    """日语文本分析器（异步版本，适用于 FastAPI 环境）

    使用LLM分析日语文本，提取：
    - 平假名（furigana）
    - 罗马字（romaji）
    - 词性（type）

    支持批量处理和并发控制。
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_concurrent: int = 10,
        batch_num: int = 5,
    ):
        """初始化分析器

        Args:
            model: LLM模型名称
            max_concurrent: 最大并发数（使用 asyncio.Semaphore 控制）
            batch_num: 每批处理的文本数量
        """
        self.model = model
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.batch_num = batch_num

    async def analyze_text(self, text: str) -> List[Dict[str, str]]:
        """分析单个日语文本，返回词级别的信息

        Args:
            text: 待分析的日语文本

        Returns:
            词信息列表，每个词包含 text, furigana, romaji, type
        """
        if not text or not text.strip():
            return []

        # 使用信号量控制并发数
        async with self.semaphore:
            try:
                return await self._analyze_with_agent_loop(text)
            except Exception as e:
                logger.error(f"分析失败: {e}")
                # 失败时返回基本结构
                return [
                    {"text": char, "furigana": "", "romaji": "", "type": "unknown"}
                    for char in text
                    if char.strip()
                ]

    async def analyze_texts(self, texts: List[str]) -> List[List[Dict[str, str]]]:
        """批量分析多个日语文本

        Args:
            texts: 待分析的日语文本列表

        Returns:
            分析结果列表，每个元素对应一个文本的分析结果
        """
        if not texts:
            return []

        # 分批处理
        chunks = self._split_chunks(texts)

        # 并行分析所有批次
        results = await self._parallel_analyze(chunks)

        # 展平结果
        flat_results = []
        for result in results:
            flat_results.extend(result)

        return flat_results

    def _split_chunks(self, texts: List[str]) -> List[List[str]]:
        """将文本列表分割成批次

        Args:
            texts: 文本列表

        Returns:
            批次列表
        """
        return [
            texts[i : i + self.batch_num] for i in range(0, len(texts), self.batch_num)
        ]

    async def _parallel_analyze(
        self, chunks: List[List[str]]
    ) -> List[List[Dict[str, str]]]:
        """并行分析所有批次

        Args:
            chunks: 文本批次列表

        Returns:
            分析结果列表
        """
        # 使用 asyncio.gather 并发执行所有任务
        tasks = [self._analyze_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        analyzed_results = []
        for i, result in enumerate[List[List[Dict[str, str]]] | BaseException](results):
            if isinstance(result, Exception):
                logger.error(f"分析批次失败：{str(result)}")
                # 失败时返回空结果列表，每个文本对应一个空列表
                analyzed_results.append([[] for _ in chunks[i]])
            else:
                analyzed_results.append(result)

        return analyzed_results

    async def _analyze_chunk(self, texts: List[str]) -> List[List[Dict[str, str]]]:
        """分析单个文本批次

        Args:
            texts: 文本批次列表

        Returns:
            分析结果列表
        """
        logger.info(f"[+]正在分析日语文本批次，共 {len(texts)} 条")

        # 使用信号量控制并发数
        async with self.semaphore:
            # 并发分析批次内的所有文本
            tasks = [self._analyze_with_agent_loop(text) for text in texts]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            analyzed_results = []
            for i, result in enumerate[List[Dict[str, str]] | BaseException](results):
                if isinstance(result, Exception):
                    logger.error(f"分析文本失败：{str(result)}")
                    # 失败时返回基本结构
                    text = texts[i]
                    analyzed_results.append(
                        [
                            {
                                "text": char,
                                "furigana": "",
                                "romaji": "",
                                "type": "unknown",
                            }
                            for char in text
                            if char.strip()
                        ]
                    )
                else:
                    analyzed_results.append(result)

            return analyzed_results

    async def _analyze_with_agent_loop(self, text: str) -> List[Dict[str, str]]:
        """使用agent loop分析文本，自动验证和修正

        Args:
            text: 待分析的日语文本

        Returns:
            词信息列表
        """
        # 计算原文字符数（去除空格）
        original_length = len(re.sub(r"\s+", "", text))

        user_prompt = (
            f"Analyze the following Japanese text and extract word-level information:\n"
            f"<text>{text}</text>\n\n"
            f"**CRITICAL REQUIREMENTS (MUST FOLLOW):**\n"
            f"1. **NO AUTO-CORRECTION (绝对禁止自动修正):**\n"
            f"   - DO NOT attempt to correct, fix, improve, or standardize the input text\n"
            f"   - DO NOT 'fix' spelling errors, typos, or non-standard usage\n"
            f"   - Even if the text appears 'wrong' or non-standard, output it EXACTLY as given\n"
            f"   - Your task is to ANALYZE the text, NOT to CORRECT it\n"
            f"   - The 'text' field MUST match the original EXACTLY, with NO modifications\n"
            f"   - Do NOT modify, delete, or replace any character, word, particle, ending, or conjugation form in the original text\n"
            f"   - Do NOT perform any form of grammatical correction or natural language completion\n"
            f"   - Keep the original text completely unchanged, every character must be preserved exactly as is\n\n"
            f"2. **ONE-TO-ONE CORRESPONDENCE (最重要):**\n"
            f"   - Every character in the input text MUST have a corresponding output item\n"
            f"   - Every output item's 'text' field MUST correspond to consecutive characters in the input\n"
            f"   - NO character can be omitted, skipped, modified, or replaced\n"
            f"   - NO character can be duplicated or added\n"
            f"   - Input and output must have a one-to-one correspondence\n\n"
            f"3. **NO MORPHEME DECOMPOSITION OR LEMMATIZATION (严格禁止形态素分解和词形还原):**\n"
            f"   - 「教師あり形態素分解禁止」- Do NOT perform supervised morpheme decomposition\n"
            f"   - Do NOT expand or transform any morpheme into another form\n"
            f"   - Do NOT split contracted forms into their theoretical sources\n"
            f"   - 禁止把「だ」→「で + ある」\n"
            f"   - 禁止把「じゃ」→「では」\n"
            f"   - 禁止把「とっ」→「と + っ」\n"
            f"   - Do NOT perform any lemmatization (禁止任何词形还原)\n"
            f"   - Every text must be EXACTLY the substring from the original input\n"
            f"   - Keep the actual form in the original text, do NOT restore to theoretical base form\n"
            f"   - Do NOT expand abbreviations to their full theoretical forms\n"
            f"   - Do NOT convert spoken forms to written forms\n"
            f"   - Do NOT restore any word to dictionary form or base form\n"
            f"   - The 'text' field MUST be an exact substring from the original, with NO transformations\n\n"
            f"4. **Word segmentation must follow Japanese grammar rules (按日语语法拆分):**\n"
            f"   - Segmentation should match how Japanese learners understand the grammar\n"
            f"   - Follow Japanese grammatical structure, NOT just part of speech\n\n"
            f"5. **Grammar-based segmentation rules:**\n"
            f"   a. **Particles (助詞)**: MUST be separated as individual words\n"
            f"      - Case particles (格助詞): が、を、に、へ、と、から、より、で、まで\n"
            f"      - Adverbial particles (副助詞): は、も、だけ、ばかり、まで、など\n"
            f"      - Conjunctive particles (接続助詞): て、で、ながら、が、けれども\n"
            f"      - Sentence-final particles (終助詞): か、ね、よ、な、わ\n"
            f"      - Example: '母親が' → '母親' + 'が'\n\n"
            f"   b. **Verbs (動詞)**: Verb stem + conjugation form as one unit\n"
            f"      - Example: '叩いた' (ta-form), '食べる' (dictionary form)\n"
            f"      - Passive/causative forms as one unit: '逮捕されました'\n\n"
            f"   c. **Auxiliary verbs (助動詞)**: Separate from main verb\n"
            f"      - 'です', 'ます', 'だ', 'ない', 'たい', 'らしい' should be separate\n"
            f"      - Example: '食べます' → '食べ' + 'ます'\n\n"
            f"   d. **Nouns (名詞)**: Complete words as one unit\n"
            f"      - Example: '母親', '勉強', '頭'\n\n"
            f"   e. **Adjectives (形容詞)**: Stem + conjugation as one unit\n"
            f"      - Example: '高い', '高かった', '高くて'\n\n"
            f"   f. **Conjunctions (接続詞)**: Separate words\n"
            f"      - Example: 'そして', 'しかし', 'だから', 'でも'\n\n"
            f"   g. **Adverbs (副詞)**: Separate words\n"
            f"      - Example: 'とても', 'すごく', 'よく'\n\n"
            f"   **Key principle**: Particles MUST be separated; verb/adjective conjugations as one unit; auxiliary verbs separated\n"
            f"6. The original text has {original_length} characters (excluding spaces).\n"
            f"7. The total length of all 'text' fields MUST be exactly {original_length} characters.\n"
            f"8. Do NOT omit any characters (including punctuation, particles, spaces).\n"
            f"9. Do NOT add any characters that are not in the original text.\n"
            f"10. Do NOT modify, replace, or correct any characters in the original text.\n"
            f"11. Before outputting, verify:\n"
            f"   - result_text = ''.join([item['text'] for item in result])\n"
            f"   - len(result_text.replace(' ', '')) == {original_length}\n"
            f"   - result_text.replace(' ', '') == '{text.replace(' ', '')}'\n"
            f"   - Every character matches exactly, with NO corrections or modifications\n\n"
            f"Return a JSON array where each element contains:\n"
            f"- text: the original word (segmented by part of speech, MUST match exactly, NO corrections, NO modifications)\n"
            f"- furigana: hiragana reading (平假名)\n"
            f"- romaji: romanized reading\n"
            f"- type: part of speech (noun, verb, adjective, particle, etc.)\n\n"
            f"**Example:**\n"
            f"Input: '母親が逮捕されました'\n"
            f"Output: [\n"
            f'  {{"text": "母親", "furigana": "ははおや", "romaji": "hahaoya", "type": "noun"}},\n'
            f'  {{"text": "が", "furigana": "が", "romaji": "ga", "type": "particle"}},\n'
            f'  {{"text": "逮捕されました", "furigana": "たいほされました", "romaji": "taihosaremashita", "type": "verb"}}\n'
            f"]\n"
            f"Verification: '母親' + 'が' + '逮捕されました' = '母親が逮捕されました' ✓ (all {len(text.replace(' ', ''))} characters covered, NO modifications)\n\n"
            f"**Verification (MANDATORY before output):**\n"
            f"1. Concatenate all 'text' fields: result_text = ''.join([item['text'] for item in result])\n"
            f"2. Compare character by character: result_text.replace(' ', '') == '{text.replace(' ', '')}'\n"
            f"3. Verify length: len(result_text.replace(' ', '')) == {original_length}\n"
            f"4. Verify NO modifications: Every character must match the original EXACTLY\n"
            f"5. If any mismatch, identify missing/extra/modified characters and correct the output\n\n"
            f"**OUTPUT FORMAT (MANDATORY):**\n"
            f"- Output ONLY a JSON array, no explanations, no markdown, no code blocks\n"
            f'- Format: [{{"text": "...", "furigana": "...", "romaji": "...", "type": "..."}}]\n'
            f'- Example: [{{"text": "母親", "furigana": "ははおや", "romaji": "hahaoya", "type": "noun"}}]'
        )

        messages = [
            {
                "role": "system",
                "content": get_prompt("analyze/japanese")
                if self._has_prompt()
                else "You are a Japanese language analyzer. Analyze Japanese text and extract word-level information including furigana, romaji, and part of speech.",
            },
            {"role": "user", "content": user_prompt},
        ]

        last_result = None

        # Agent loop
        for step in range(MAX_STEPS):
            # 调用LLM（使用 asyncio.to_thread 包装同步调用）
            response = await asyncio.to_thread(
                call_llm,
                messages=messages,
                model=self.model,
                temperature=0.1,
            )

            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("LLM返回空结果")

            # 解析结果
            try:
                parsed_result = json_repair.loads(result_text)
                if not isinstance(parsed_result, list):
                    raise ValueError(f"期望list，实际{type(parsed_result)}")

                result_list: List[Dict[str, str]] = parsed_result
                last_result = result_list

                # 验证结果
                is_valid, error_message = self._validate_result(text, result_list)

                if is_valid:
                    return result_list

                # 验证失败，添加反馈
                logger.warning(
                    f"分析验证失败，开始反馈循环 (第{step + 1}次尝试): {error_message}"
                )
                messages.append({"role": "assistant", "content": result_text})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Validation failed: {error_message}\n"
                            f"Please fix the errors and output ONLY a valid JSON array."
                        ),
                    }
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"解析失败 (第{step + 1}次尝试): {str(e)}")
                messages.append({"role": "assistant", "content": result_text})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Invalid JSON format: {str(e)}\n"
                            f"Please output ONLY a valid JSON array."
                        ),
                    }
                )

        # 达到最大步数
        logger.warning(f"达到最大尝试次数({MAX_STEPS})，返回最后结果")
        return last_result if last_result else []

    def _validate_result(
        self, original_text: str, result: List[Dict[str, str]]
    ) -> Tuple[bool, str]:
        """验证分析结果

        Args:
            original_text: 原始文本
            result: 分析结果列表

        Returns:
            (是否有效, 错误消息)
        """
        if not result:
            return False, "结果为空"

        # 检查必需字段
        required_fields = ["text", "furigana", "romaji", "type"]
        for i, item in enumerate(result):
            if not isinstance(item, dict):
                return False, f"第{i + 1}项不是字典类型"
            for field in required_fields:
                if field not in item:
                    return False, f"第{i + 1}项缺少字段: {field}"

        # 检查文本是否匹配（必须完全匹配）
        result_text = "".join(item.get("text", "") for item in result)
        original_cleaned = re.sub(r"\s+", "", original_text)
        result_cleaned = re.sub(r"\s+", "", result_text)

        # 严格检查长度必须完全一致
        if len(original_cleaned) != len(result_cleaned):
            # 使用字符频率分析找出缺失或多余的字符
            from collections import Counter

            original_counter = Counter(original_cleaned)
            result_counter = Counter(result_cleaned)

            missing_chars = []
            for char, count in original_counter.items():
                result_count = result_counter.get(char, 0)
                if count > result_count:
                    missing_chars.extend([char] * (count - result_count))

            extra_chars = []
            for char, count in result_counter.items():
                original_count = original_counter.get(char, 0)
                if count > original_count:
                    extra_chars.extend([char] * (count - original_count))

            error_msg = f"文本长度不匹配: 原文{len(original_cleaned)}字符，结果{len(result_cleaned)}字符，差异{abs(len(original_cleaned) - len(result_cleaned))}字符"
            if missing_chars:
                error_msg += (
                    f"\n缺失的字符（共{len(missing_chars)}个）: {missing_chars[:20]}"
                )
            if extra_chars:
                error_msg += (
                    f"\n多余的字符（共{len(extra_chars)}个）: {extra_chars[:20]}"
                )
            error_msg += f"\n\n请确保所有字符都被包含在结果中。原文: '{original_text}'"
            return False, error_msg

        # 验证字符顺序和内容是否匹配（使用字符序列比较）
        if original_cleaned != result_cleaned:
            # 使用 difflib 找出具体差异
            import difflib

            diff = list(
                difflib.unified_diff([original_cleaned], [result_cleaned], lineterm="")
            )
            if diff:
                error_msg = f"文本内容不匹配（长度相同但内容不同）\n原文: '{original_cleaned}'\n结果: '{result_cleaned}'"
                return False, error_msg

        return True, ""

    def _has_prompt(self) -> bool:
        """检查是否存在分析提示词文件"""
        try:
            get_prompt("analyze/japanese")
            return True
        except (FileNotFoundError, Exception):
            return False
