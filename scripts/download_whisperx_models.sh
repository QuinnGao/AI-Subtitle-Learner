#!/bin/bash
# WhisperX 模型下载脚本
# 下载 WhisperX 所需的所有模型到项目 models 目录

set -e  # 遇到错误立即退出

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODELS_DIR="$PROJECT_ROOT/models"
WHISPERX_DIR="$MODELS_DIR/whisperx"

# 创建模型目录
echo "创建模型目录: $WHISPERX_DIR"
mkdir -p "$WHISPERX_DIR"

# 进入模型目录
cd "$WHISPERX_DIR"

echo "=========================================="
echo "开始下载 WhisperX 模型"
echo "模型存储目录: $WHISPERX_DIR"
echo "=========================================="
echo ""

# 1. 下载 Whisper large-v3 模型
echo "1. 下载 Whisper large-v3 模型..."
if [ -d "whisper-large-v3" ]; then
    echo "   whisper-large-v3 已存在，跳过下载"
    echo "   如需重新下载，请先删除: rm -rf $WHISPERX_DIR/whisper-large-v3"
else
    echo "   正在克隆 https://huggingface.co/openai/whisper-large-v3"
    git clone https://huggingface.co/openai/whisper-large-v3
    echo "   ✓ Whisper large-v3 下载完成"
fi
echo ""

# 2. 下载 Silero VAD 模型
echo "2. 下载 Silero VAD 模型..."
if [ -d "silero" ]; then
    echo "   silero 已存在，跳过下载"
    echo "   如需重新下载，请先删除: rm -rf $WHISPERX_DIR/silero"
else
    echo "   正在克隆 https://huggingface.co/silero-vad/models"
    git clone https://huggingface.co/silero-vad/models silero
    echo "   ✓ Silero VAD 模型下载完成"
fi
echo ""

# 3. 下载 wav2vec2 模型
echo "3. 下载 wav2vec2 模型..."
if [ -d "wav2vec2" ]; then
    echo "   wav2vec2 已存在，跳过下载"
    echo "   如需重新下载，请先删除: rm -rf $WHISPERX_DIR/wav2vec2"
else
    echo "   正在克隆 https://huggingface.co/facebook/wav2vec2-large-960h-lv60-self"
    git clone https://huggingface.co/facebook/wav2vec2-large-960h-lv60-self wav2vec2
    echo "   ✓ wav2vec2 模型下载完成"
fi
echo ""

echo "=========================================="
echo "所有模型下载完成！"
echo "模型存储位置: $WHISPERX_DIR"
echo ""
echo "目录结构:"
ls -lh "$WHISPERX_DIR" | grep "^d" || echo "  (无子目录)"
echo "=========================================="

