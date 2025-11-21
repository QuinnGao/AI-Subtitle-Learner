#!/usr/bin/env python3
"""
提前下载 WhisperX 模型脚本
用于在首次使用前下载模型，避免运行时延迟
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import whisperx
    import torch
except ImportError:
    print("错误: WhisperX 未安装。请运行: pip install whisperx")
    sys.exit(1)

from app.core.utils.logger import setup_logger
from app.config import MODEL_PATH

logger = setup_logger("download_whisperx_models")


def download_whisper_model(
    model_name: str = "large-v3", device: str = "cpu", download_root: str = None
):
    """下载 Whisper 模型"""
    logger.info(f"开始下载 Whisper 模型: {model_name}")
    print(f"正在下载 Whisper 模型: {model_name}...")

    try:
        # 自动检测设备
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA 不可用，使用 CPU")
            device = "cpu"
            compute_type = "float32"
        else:
            compute_type = "float16" if device == "cuda" else "float32"

        # 确定模型目录
        if not download_root:
            # 使用项目根目录下的 models/whisperx 文件夹
            download_root = str(MODEL_PATH / "whisperx")
            Path(download_root).mkdir(parents=True, exist_ok=True)

        logger.info(f"模型下载目录: {download_root}")
        print(f"模型下载目录: {download_root}")

        # 加载模型（会自动下载）
        model = whisperx.load_model(
            model_name,
            device=device,
            compute_type=compute_type,
            download_root=download_root,
        )

        logger.info(f"Whisper 模型下载完成: {model_name}")
        print(f"✓ Whisper 模型下载完成: {model_name}")
        return True
    except Exception as e:
        logger.error(f"下载 Whisper 模型失败: {str(e)}", exc_info=True)
        print(f"✗ 下载 Whisper 模型失败: {str(e)}")
        return False


def download_align_models(languages: list[str] = None):
    """下载对齐模型（用于词级时间戳）"""
    if languages is None:
        # 常用语言
        languages = ["en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru"]

    logger.info(f"开始下载对齐模型，语言: {languages}")
    print(f"正在下载对齐模型，语言: {languages}...")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    success_count = 0

    for lang in languages:
        try:
            logger.info(f"下载对齐模型: {lang}")
            print(f"  下载对齐模型: {lang}...", end=" ")

            model_a, metadata = whisperx.load_align_model(
                language_code=lang, device=device
            )

            logger.info(f"对齐模型下载完成: {lang}")
            print("✓")
            success_count += 1
        except Exception as e:
            logger.warning(f"下载对齐模型失败 ({lang}): {str(e)}")
            print(f"✗ ({str(e)})")

    logger.info(f"对齐模型下载完成: {success_count}/{len(languages)}")
    print(f"✓ 对齐模型下载完成: {success_count}/{len(languages)}")
    return success_count == len(languages)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="提前下载 WhisperX 模型")
    parser.add_argument(
        "--model",
        type=str,
        default="large-v3",
        help="Whisper 模型名称 (默认: large-v3)",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="设备 (cuda/cpu/auto, 默认: cpu)",
        choices=["cuda", "cpu", "auto"],
    )
    parser.add_argument(
        "--languages",
        type=str,
        nargs="+",
        default=None,
        help="要下载的对齐模型语言代码列表 (默认: 常用语言)",
    )
    parser.add_argument(
        "--skip-align",
        action="store_true",
        help="跳过对齐模型下载",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=None,
        help="模型存储目录 (默认: models/whisperx)",
    )

    args = parser.parse_args()

    # 确定设备
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    # 确定模型目录
    if args.model_dir:
        download_root = args.model_dir
    else:
        download_root = str(MODEL_PATH / "whisperx")

    Path(download_root).mkdir(parents=True, exist_ok=True)

    print(f"使用设备: {device}")
    print(f"Whisper 模型: {args.model}")
    print(f"模型存储目录: {download_root}")
    print("-" * 60)

    # 下载 Whisper 模型
    success = download_whisper_model(args.model, device, download_root)
    if not success:
        print("Whisper 模型下载失败，退出")
        sys.exit(1)

    print("-" * 60)

    # 下载对齐模型
    if not args.skip_align:
        download_align_models(args.languages)

    print("-" * 60)
    print("所有模型下载完成！")
    logger.info("所有模型下载完成")


if __name__ == "__main__":
    main()
