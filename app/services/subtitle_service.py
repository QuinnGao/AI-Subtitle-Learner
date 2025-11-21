"""
字幕处理服务
"""

import os
import sys
from pathlib import Path
import json

from app.schemas.subtitle import SubtitleRequest
from app.services.task_manager import get_task_manager
from app.core.asr.asr_data import ASRData
from app.core.entities import SubtitleConfig as CoreSubtitleConfig
from app.core.analyze.japanese_analyzer import JapaneseAnalyzer
from app.core.split.split import SubtitleSplitter
from app.core.optimize.optimize import SubtitleOptimizer
from app.core.translate import (
    BingTranslator,
    DeepLXTranslator,
    GoogleTranslator,
    LLMTranslator,
)
from app.core.llm.health_check import get_health_checker
from app.core.utils.logger import setup_logger
from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL, CACHE_PATH

task_manager = get_task_manager()
logger = setup_logger("subtitle_service")

# 字幕处理缓存目录
SUBTITLE_CACHE_DIR = CACHE_PATH / "subtitle_processing"
SUBTITLE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class SubtitleService:
    """字幕处理服务"""

    def __init__(self):
        self.task_manager = task_manager
        self.cache_dir = SUBTITLE_CACHE_DIR

    def _get_cache_file_path(
        self, step: str, subtitle_path: str, config: CoreSubtitleConfig
    ) -> Path:
        """获取缓存文件路径

        Args:
            step: 步骤名称（split, optimize, analyze_japanese, translate）
            subtitle_path: 字幕文件路径
            config: 配置对象

        Returns:
            缓存文件路径
        """
        # 基于文件名生成缓存文件名
        file_path = Path(subtitle_path)
        file_stem = file_path.stem

        # 构建配置标识（用于区分不同配置的缓存）
        config_parts = []
        if step == "split":
            config_parts = [
                f"cjk{config.max_word_count_cjk}",
                f"en{config.max_word_count_english}",
                config.llm_model or "default",
            ]
        elif step == "optimize":
            config_parts = [
                config.llm_model or "default",
                config.custom_prompt_text[:20]
                if config.custom_prompt_text
                else "default",
            ]
        elif step == "analyze_japanese":
            config_parts = [
                config.llm_model or "default",
            ]
        elif step == "translate":
            config_parts = [
                config.translator_service.value
                if config.translator_service
                else "default",
                config.target_language.value if config.target_language else "default",
                config.llm_model or "default",
                "reflect" if config.need_reflect else "normal",
            ]
        elif step == "add_timestamps":
            # add_timestamps 步骤不依赖配置，使用固定标识
            config_parts = ["v1"]
        elif step == "result":
            # result 步骤包含所有配置信息
            config_parts = [
                f"cjk{config.max_word_count_cjk}" if config.need_split else "nosplit",
                f"en{config.max_word_count_english}"
                if config.need_split
                else "nosplit",
                config.llm_model or "default",
                "analyze" if config.need_analyze_japanese else "noanalyze",
                config.translator_service.value
                if config.need_translate and config.translator_service
                else "notranslate",
                config.target_language.value
                if config.need_translate and config.target_language
                else "notranslate",
            ]

        config_hash = "_".join(config_parts).replace("/", "_").replace("\\", "_")

        # 缓存文件名格式: {原文件名}_{步骤}_{配置标识}.json
        cache_filename = f"{file_stem}_{step}_{config_hash}.json"

        return self.cache_dir / cache_filename

    def _load_from_cache(self, cache_path: Path):
        """从缓存文件加载数据

        Args:
            cache_path: 缓存文件路径

        Returns:
            缓存的数据，如果文件不存在则返回 None
        """
        if cache_path.exists():
            try:
                import json

                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存失败: {cache_path}, 错误: {e}")
                return None
        return None

    def _save_to_cache(self, cache_path: Path, data):
        """保存数据到缓存文件

        Args:
            cache_path: 缓存文件路径
            data: 要保存的数据（必须是可 JSON 序列化的）
        """
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败: {cache_path}, 错误: {e}")

    def _validate_subtitle_file(self, task_id: str, subtitle_path: Path) -> None:
        """验证字幕文件是否存在"""
        logger.info(f"[任务 {task_id}] 验证字幕文件: {subtitle_path}")
        sys.stderr.flush()
        if not subtitle_path.exists():
            error_msg = f"字幕文件不存在: {subtitle_path}"
            logger.error(f"[任务 {task_id}] {error_msg}")
            sys.stderr.flush()
            raise ValueError(error_msg)
        logger.info(f"[任务 {task_id}] 字幕文件验证通过: {subtitle_path}")
        sys.stderr.flush()

    def _prepare_config(self, task_id: str, config) -> CoreSubtitleConfig:
        """准备配置（使用环境变量默认值并转换）"""
        # 如果配置中没有 LLM 信息，使用环境变量中的默认值
        if not config.base_url and LLM_API_BASE:
            config.base_url = LLM_API_BASE
        if not config.api_key and LLM_API_KEY:
            config.api_key = LLM_API_KEY
        if not config.llm_model and LLM_MODEL:
            config.llm_model = LLM_MODEL

        core_config = self._convert_config(config)
        logger.debug(
            f"[任务 {task_id}] 配置转换完成: need_translate={core_config.need_translate}, "
            f"need_optimize={core_config.need_optimize}, need_split={core_config.need_split}, "
            f"llm_model={core_config.llm_model or '未配置'}"
        )
        return core_config

    def _load_subtitle_data(self, task_id: str, subtitle_path: Path) -> ASRData:
        """加载字幕数据"""
        logger.info(f"[任务 {task_id}] 加载字幕文件: {subtitle_path}")
        asr_data = ASRData.from_subtitle_file(str(subtitle_path))
        logger.info(
            f"[任务 {task_id}] 字幕加载完成，共 {len(asr_data.segments)} 条字幕"
        )
        return asr_data

    def _calculate_output_name(self, subtitle_path: Path) -> str:
        """计算输出文件名"""
        return subtitle_path.stem.replace("【原始字幕】", "").replace(
            "【下载字幕】", ""
        )

    def _validate_llm_config(
        self, task_id: str, core_config: CoreSubtitleConfig, asr_data: ASRData
    ) -> None:
        """验证 LLM 配置（如果需要 LLM）"""
        if self._need_llm(core_config, asr_data):
            logger.info(f"[任务 {task_id}] 需要 LLM，开始验证 LLM 配置")
            self.task_manager.update_task(task_id, progress=2, message="验证 LLM 配置")
            # 使用健康检查器验证并设置 LLM 配置（全局统一处理，自动处理错误）
            # 从环境变量获取配置
            health_checker = get_health_checker()
            health_checker.ensure_healthy(force=False)

    async def _process_split(
        self,
        task_id: str,
        subtitle_path: Path,
        asr_data: ASRData,
        core_config: CoreSubtitleConfig,
        output_name: str,
    ) -> ASRData:
        """处理重新断句（对于字词级字幕）"""
        if not asr_data.is_word_timestamp():
            return asr_data

        cache_path = self._get_cache_file_path("split", str(subtitle_path), core_config)
        split_path = str(subtitle_path.parent / f"【断句字幕】{output_name}.srt")

        # 检查缓存
        cached_data = self._load_from_cache(cache_path)
        if cached_data:
            logger.info(f"[任务 {task_id}] 使用缓存的断句结果: {cache_path}")
            asr_data = ASRData.from_json(cached_data)
            asr_data.save(save_path=split_path)
            logger.info(f"[任务 {task_id}] 断句完成（使用缓存），保存到: {split_path}")
        else:
            logger.info(f"[任务 {task_id}] 开始重新断句（字词级字幕）")
            self.task_manager.update_task(task_id, progress=10, message="字幕断句中")
            splitter = SubtitleSplitter(
                max_concurrent=core_config.thread_num,
                model=core_config.llm_model,
                max_word_count_cjk=core_config.max_word_count_cjk,
                max_word_count_english=core_config.max_word_count_english,
            )
            asr_data = await splitter.split_subtitle(asr_data)
            asr_data.save(save_path=split_path)
            # 保存到缓存
            self._save_to_cache(cache_path, asr_data.to_json())
            logger.info(
                f"[任务 {task_id}] 断句完成，保存到: {split_path}，已缓存到: {cache_path}"
            )

        return asr_data

    async def _process_analyze_japanese(
        self,
        task_id: str,
        subtitle_path: Path,
        asr_data: ASRData,
        core_config: CoreSubtitleConfig,
    ) -> ASRData:
        """处理日语文本分析"""
        if not core_config.need_analyze_japanese:
            return asr_data

        cache_path = self._get_cache_file_path(
            "analyze_japanese", str(subtitle_path), core_config
        )

        # 检查缓存
        cached_data = self._load_from_cache(cache_path)
        if cached_data:
            logger.info(f"[任务 {task_id}] 使用缓存的日语分析结果: {cache_path}")
            # 恢复 tokens 数据
            for i, seg in enumerate(asr_data.segments):
                if i < len(cached_data) and cached_data[i]:
                    seg.tokens = cached_data[i]
            logger.info(f"[任务 {task_id}] 日语文本分析完成（使用缓存）")
        else:
            logger.info(f"[任务 {task_id}] 开始分析日语文本")
            self.task_manager.update_task(
                task_id, progress=55, message="分析日语文本中"
            )
            analyzer = JapaneseAnalyzer(
                model=core_config.llm_model,
                max_concurrent=core_config.thread_num,
                batch_num=core_config.batch_size,
            )

            # 收集需要分析的文本
            texts_to_analyze = []
            segment_indices = []
            for i, seg in enumerate(asr_data.segments):
                if seg.text and seg.text.strip():
                    texts_to_analyze.append(seg.text)
                    segment_indices.append(i)

            # 批量分析
            if texts_to_analyze:
                results = await analyzer.analyze_texts(texts_to_analyze)
                # 将结果分配回对应的segment
                for idx, tokens in zip(segment_indices, results):
                    asr_data.segments[idx].tokens = tokens

                # 保存到缓存（只保存 tokens 数据）
                tokens_cache = [None] * len(asr_data.segments)
                for idx, tokens in zip(segment_indices, results):
                    tokens_cache[idx] = tokens
                self._save_to_cache(cache_path, tokens_cache)
                logger.info(
                    f"[任务 {task_id}] 日语文本分析完成，已缓存到: {cache_path}"
                )
            else:
                logger.info(f"[任务 {task_id}] 日语文本分析完成（无文本需要分析）")

        return asr_data

    def _add_timestamps_to_tokens(
        self,
        task_id: str,
        subtitle_path: Path,
        asr_data: ASRData,
        core_config: CoreSubtitleConfig,
    ) -> ASRData:
        """根据 word_segments 的时间戳为 tokens 添加开始和结束时间"""
        logger.info(f"[任务 {task_id}] 开始为 tokens 添加时间戳")

        for seg_idx, seg in enumerate(asr_data.segments):
            if not seg.tokens or not seg.word_segments:
                continue

            # 构建完整的文本用于验证
            tokens_text = "".join([token.get("text", "") for token in seg.tokens])
            word_segs_text = "".join([ws.text for ws in seg.word_segments])

            # 如果文本不匹配，跳过（可能是分析结果与原始文本不一致）
            if tokens_text.replace(" ", "") != word_segs_text.replace(" ", ""):
                logger.debug(
                    f"[任务 {task_id}] Segment {seg_idx} 文本不匹配，跳过时间戳添加"
                )
                continue

            # 按顺序匹配：使用累积文本匹配策略
            # 一个 token 可能对应一个或多个 word_segment
            word_seg_index = 0
            token_start_index = 0  # 当前 token 对应的第一个 word_segment 索引

            for token_idx, token in enumerate(seg.tokens):
                token_text = token.get("text", "").strip()
                if not token_text:
                    continue

                # 累积 tokens 的文本
                tokens_accumulated = "".join(
                    [
                        t.get("text", "")
                        for t in seg.tokens[token_start_index : token_idx + 1]
                    ]
                )

                # 累积 word_segments 的文本直到匹配
                word_segs_accumulated = ""
                word_seg_end_index = word_seg_index

                while word_seg_end_index < len(seg.word_segments):
                    word_seg = seg.word_segments[word_seg_end_index]
                    word_segs_accumulated += word_seg.text

                    # 检查是否匹配
                    if tokens_accumulated == word_segs_accumulated:
                        # 完全匹配，使用第一个和最后一个 word_segment 的时间戳
                        token["start_time"] = seg.word_segments[
                            word_seg_index
                        ].start_time
                        token["end_time"] = word_seg.end_time
                        word_seg_index = word_seg_end_index + 1
                        token_start_index = token_idx + 1
                        break
                    elif len(tokens_accumulated) < len(word_segs_accumulated):
                        # word_segments 文本更长，需要更多 tokens，继续下一个 token
                        break
                    else:
                        # tokens 文本更长，需要更多 word_segments
                        word_seg_end_index += 1

        # 保存到缓存（直接保存完整的 asr_data）
        cache_path = self._get_cache_file_path(
            "add_timestamps", str(subtitle_path), core_config
        )
        self._save_to_cache(cache_path, asr_data.to_json())
        logger.info(f"[任务 {task_id}] tokens 时间戳添加完成，已缓存到: {cache_path}")

        return asr_data

    async def _process_translate(
        self,
        task_id: str,
        subtitle_path: Path,
        asr_data: ASRData,
        core_config: CoreSubtitleConfig,
    ) -> ASRData:
        """处理字幕翻译"""
        if not core_config.need_translate:
            return asr_data

        cache_path = self._get_cache_file_path(
            "translate", str(subtitle_path), core_config
        )

        # 检查缓存
        cached_data = self._load_from_cache(cache_path)
        if cached_data:
            logger.info(f"[任务 {task_id}] 使用缓存的翻译结果: {cache_path}")
            asr_data = ASRData.from_json(cached_data)
            logger.info(f"[任务 {task_id}] 字幕翻译完成（使用缓存）")
        else:
            logger.info(
                f"[任务 {task_id}] 开始翻译字幕，目标语言: {core_config.target_language}, "
                f"翻译服务: {core_config.translator_service}"
            )
            self.task_manager.update_task(task_id, progress=60, message="翻译字幕中")
            if not core_config.target_language:
                error_msg = "目标语言未配置"
                logger.error(f"[任务 {task_id}] {error_msg}")
                raise Exception(error_msg)

            subtitle_length = len(asr_data.segments)
            finished_subtitle_length = [0]  # 使用列表以便在回调中修改

            translator = self._get_translator(
                core_config,
                lambda result: self._translate_callback(
                    result,
                    task_id,
                    subtitle_length,
                    finished_subtitle_length,
                ),
            )
            logger.debug(
                f"[任务 {task_id}] 翻译器创建成功: {type(translator).__name__}"
            )
            asr_data = translator.translate_subtitle(asr_data)
            asr_data.remove_punctuation()
            # 保存到缓存
            self._save_to_cache(cache_path, asr_data.to_json())
            logger.info(f"[任务 {task_id}] 字幕翻译完成，已缓存到: {cache_path}")

        return asr_data

    def _save_result(
        self,
        task_id: str,
        subtitle_path: Path,
        asr_data: ASRData,
        core_config: CoreSubtitleConfig,
    ) -> str:
        """保存处理结果到缓存"""
        # 保存到缓存
        cache_path = self._get_cache_file_path(
            "result", str(subtitle_path), core_config
        )
        json_data = asr_data.to_json()
        self._save_to_cache(cache_path, json_data)
        logger.info(f"[任务 {task_id}] 保存 JSON 结果到缓存: {cache_path}")

        return str(cache_path)

    async def process_subtitle_task(self, task_id: str, request: SubtitleRequest):
        """处理字幕任务"""
        # 立即输出日志，确保在 Docker 中可见
        logger.info(f"[任务 {task_id}] 开始处理字幕任务")
        sys.stderr.flush()  # 立即刷新输出，确保后台任务日志可见

        logger.debug(
            f"[任务 {task_id}] 请求参数: subtitle_path={request.subtitle_path}, "
            f"video_path={request.video_path}, output_path={request.output_path}"
        )

        try:
            self.task_manager.update_task(
                task_id, status="running", message="开始处理字幕"
            )

            # 1. 验证文件
            subtitle_path = Path(request.subtitle_path)
            self._validate_subtitle_file(task_id, subtitle_path)

            # 2. 准备配置
            core_config = self._prepare_config(task_id, request.config)

            # 3. 加载字幕数据
            asr_data = self._load_subtitle_data(task_id, subtitle_path)

            # 4. 计算输出文件名
            output_name = self._calculate_output_name(subtitle_path)

            # 5. 验证 LLM 配置（如果需要 LLM）
            self._validate_llm_config(task_id, core_config, asr_data)

            # 6. 重新断句（对于字词级字幕）
            asr_data = await self._process_split(
                task_id, subtitle_path, asr_data, core_config, output_name
            )

            # 7. 分析日语文本
            asr_data = await self._process_analyze_japanese(
                task_id, subtitle_path, asr_data, core_config
            )

            # 8. 为 tokens 添加时间戳（基于 word_segments）
            asr_data = self._add_timestamps_to_tokens(
                task_id, subtitle_path, asr_data, core_config
            )

            # 9. 翻译字幕
            asr_data = await self._process_translate(
                task_id, subtitle_path, asr_data, core_config
            )

            # 10. 保存结果
            json_output_path = self._save_result(
                task_id, subtitle_path, asr_data, core_config
            )

            logger.info(f"[任务 {task_id}] 字幕处理完成，输出文件: {json_output_path}")
            sys.stderr.flush()
            self.task_manager.update_task(
                task_id,
                status="completed",
                progress=100,
                message="字幕处理完成",
                output_path=json_output_path,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[任务 {task_id}] 字幕处理失败: {error_msg}", exc_info=True)
            sys.stderr.flush()  # 确保错误日志立即输出
            self.task_manager.update_task(
                task_id, status="failed", error=error_msg, message="字幕处理失败"
            )

    def _convert_config(self, config) -> CoreSubtitleConfig:
        """转换配置格式"""
        from app.core.entities import (
            TranslatorServiceEnum,
            SubtitleLayoutEnum,
        )

        return CoreSubtitleConfig(
            base_url=config.base_url,
            api_key=config.api_key,
            llm_model=config.llm_model,
            deeplx_endpoint=config.deeplx_endpoint,
            translator_service=TranslatorServiceEnum[
                config.translator_service.value.upper()
            ]
            if config.translator_service
            else None,
            need_translate=config.need_translate,
            need_optimize=config.need_optimize,
            need_reflect=config.need_reflect,
            need_analyze_japanese=config.need_analyze_japanese,
            thread_num=config.thread_num,
            batch_size=config.batch_size,
            subtitle_layout=SubtitleLayoutEnum[config.subtitle_layout.value.upper()],
            max_word_count_cjk=config.max_word_count_cjk,
            max_word_count_english=config.max_word_count_english,
            need_split=config.need_split,
            target_language=config.target_language,
            subtitle_style=config.subtitle_style,
            custom_prompt_text=config.custom_prompt_text,
        )

    def _need_llm(self, config, asr_data):
        """判断是否需要 LLM"""
        from app.core.entities import TranslatorServiceEnum

        return (
            config.need_optimize
            or asr_data.is_word_timestamp()
            or config.need_analyze_japanese
            or (
                config.need_translate
                and config.translator_service
                not in [
                    TranslatorServiceEnum.DEEPLX,
                    TranslatorServiceEnum.BING,
                    TranslatorServiceEnum.GOOGLE,
                ]
            )
        )

    def _get_translator(self, config, callback=None):
        """获取翻译器实例"""
        from app.core.entities import TranslatorServiceEnum

        logger.debug(
            f"创建翻译器: service={config.translator_service}, "
            f"target_language={config.target_language}"
        )

        if config.translator_service == TranslatorServiceEnum.OPENAI:
            # llm_model 已在 ensure_healthy 中验证，无需重复检查
            return LLMTranslator(
                thread_num=config.thread_num,
                batch_num=config.batch_size,
                target_language=config.target_language,
                model=config.llm_model,
                custom_prompt=config.custom_prompt_text or "",
                is_reflect=config.need_reflect,
                update_callback=callback,
            )
        elif config.translator_service == TranslatorServiceEnum.DEEPLX:
            os.environ["DEEPLX_ENDPOINT"] = config.deeplx_endpoint or ""
            return DeepLXTranslator(
                thread_num=config.thread_num,
                batch_num=5,
                target_language=config.target_language,
                timeout=20,
                update_callback=callback,
            )
        elif config.translator_service == TranslatorServiceEnum.BING:
            return BingTranslator(
                thread_num=config.thread_num,
                batch_num=10,
                target_language=config.target_language,
                update_callback=callback,
            )
        elif config.translator_service == TranslatorServiceEnum.GOOGLE:
            return GoogleTranslator(
                thread_num=config.thread_num,
                batch_num=5,
                target_language=config.target_language,
                timeout=20,
                update_callback=callback,
            )
        else:
            raise ValueError(f"不支持的翻译服务: {config.translator_service}")

    def _optimize_callback(
        self, result, task_id: str, subtitle_length: int, finished_subtitle_length: list
    ):
        """优化进度回调函数"""
        finished_subtitle_length[0] += len(result)
        progress = min(int((finished_subtitle_length[0] / subtitle_length) * 100), 100)
        self.task_manager.update_task(
            task_id,
            progress=30 + int(progress * 0.2),
            message=f"优化进度: {progress}%",
        )

    def _translate_callback(
        self, result, task_id: str, subtitle_length: int, finished_subtitle_length: list
    ):
        """翻译进度回调函数"""
        finished_subtitle_length[0] += len(result)
        progress = min(int((finished_subtitle_length[0] / subtitle_length) * 100), 100)
        self.task_manager.update_task(
            task_id,
            progress=60 + int(progress * 0.3),
            message=f"翻译进度: {progress}%",
        )
