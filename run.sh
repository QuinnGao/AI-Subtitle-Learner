#!/bin/bash
# 使用 uv 运行 FastAPI 应用

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    uv venv --python 3.12
fi

# 安装依赖（如果需要）
if [ ! -f ".venv/.installed" ]; then
    echo "安装依赖..."
    uv pip install -r requirements.txt
    touch .venv/.installed
fi

# 运行应用
echo "启动 FastAPI 应用..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

