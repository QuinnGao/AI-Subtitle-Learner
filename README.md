# 视频字幕处理 API

这是一个基于 FastAPI 构建的视频字幕处理后端服务，提供视频转录、字幕处理、视频合成等功能。

## 技术栈

- **FastAPI**: 现代、快速的 Web 框架，用于构建 API
- **Python 3.12**: 编程语言
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证和设置管理

## 项目特性

- 🚀 高性能异步 API
- 📝 自动生成 API 文档（Swagger UI 和 ReDoc）
- 🔒 类型提示和数据验证
- 🎬 视频转录：支持多种 ASR 模型（Whisper、Faster Whisper 等）
- 🌐 字幕翻译：支持多种翻译服务（OpenAI、DeepLX、Bing、Google）
- ✂️ 字幕处理：自动分割、优化、翻译
- 🎥 视频合成：将字幕合成到视频中
- 📦 批量处理：支持批量处理多个文件
- 🔄 异步任务：后台任务处理，支持进度查询

## 快速开始

### 1. 环境要求

- Python 3.12
- uv（现代 Python 包管理器）

### 2. 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv

# 或使用 Homebrew (macOS)
brew install uv
```

### 3. 创建虚拟环境

```bash
# 使用 uv 创建虚拟环境（默认创建 .venv 目录）
# 指定 Python 3.12 版本
uv venv --python 3.12

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 4. 安装依赖

```bash
# 使用 uv 安装依赖（推荐，速度更快）
uv pip install fastapi uvicorn[standard]
```

或者创建 `requirements.txt` 文件：

```txt
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-multipart>=0.0.6
```

然后安装：

```bash
uv pip install -r requirements.txt
```

**提示**：使用 `uv` 时，也可以不激活虚拟环境，直接使用 `uv run` 运行命令：

```bash
# 无需激活虚拟环境，直接运行
uv run uvicorn app.main:app --reload
```

### 6. 运行应用

#### 方法 1：使用 uv run（推荐）

```bash
# 直接运行，无需激活虚拟环境
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 方法 2：使用运行脚本

```bash
# 使用提供的运行脚本
./run.sh
```

#### 方法 3：激活虚拟环境后运行

```bash
# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

# 运行应用
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

应用启动后，访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 5. 创建项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口
│   ├── models/          # 数据模型
│   ├── routers/         # API 路由
│   ├── schemas/         # Pydantic 模式
│   └── services/        # 业务逻辑
├── requirements.txt
├── .env                 # 环境变量（可选）
└── README.md
```

### 6. 安装项目依赖

项目已经包含了完整的代码结构，直接安装依赖即可：

```bash
# 安装 FastAPI 和相关依赖
uv pip install fastapi uvicorn[standard] pydantic pydantic-settings python-multipart

# 安装项目所需的其他依赖（根据 core 模块的需求）
# 例如：faster-whisper, openai, requests 等
```

### 7. 配置环境变量

创建 `.env` 文件（可选）：

```env
# 应用配置
DEBUG=False
LOG_LEVEL=INFO
WORK_DIR=./workspace
MODEL_DIR=./models

# LLM 配置（可选，支持多种环境变量名称）
# 新格式（推荐）
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o-mini

# 兼容旧格式（可选）
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini

# 翻译服务配置（可选）
DEEPLX_ENDPOINT=http://localhost:1188
```

### 8. 提前下载 WhisperX 模型（可选但推荐）

如果使用 WhisperX 进行转录，建议提前下载模型以避免首次使用时的延迟。

#### 方法 1: 使用 Shell 脚本下载（推荐）

使用 Git 直接下载模型文件到 `models/whisperx/` 目录：

```bash
# 下载所有 WhisperX 模型（Whisper、Silero VAD、wav2vec2）
./scripts/download_whisperx_models.sh

# 或使用 bash
bash scripts/download_whisperx_models.sh
```

脚本会自动：
- 创建 `models/whisperx/` 目录
- 下载 `whisper-large-v3` 模型
- 下载 `silero-vad` 模型
- 下载 `wav2vec2` 模型
- 如果模型已存在，会跳过下载

#### 方法 2: 使用 Python 脚本下载

使用 Python 脚本通过 WhisperX API 下载模型：

```bash
# 使用 uv 执行（推荐）
uv run python scripts/download_whisperx_models.py

# 或使用 python
python scripts/download_whisperx_models.py

# 或使用 python3
python3 scripts/download_whisperx_models.py
```

#### 高级选项（Python 脚本）

```bash
# 下载指定模型
uv run python scripts/download_whisperx_models.py --model large-v2

# 指定设备（cuda/cpu/auto）
uv run python scripts/download_whisperx_models.py --model large-v3 --device cuda

# 只下载 Whisper 模型，跳过对齐模型
uv run python scripts/download_whisperx_models.py --model large-v3 --skip-align

# 下载指定语言的对齐模型
uv run python scripts/download_whisperx_models.py --model large-v3 --languages en zh ja ko

# 指定自定义模型目录
uv run python scripts/download_whisperx_models.py --model-dir /path/to/models
```

### 9. 运行应用

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

应用将在 `http://localhost:8000` 启动。

## API 文档

启动应用后，可以访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 端点

### 健康检查
- `GET /health` - 健康检查

### 转录相关
- `POST /api/v1/transcribe` - 创建转录任务
- `GET /api/v1/transcribe/{task_id}` - 查询转录任务状态
- `GET /api/v1/transcribe/{task_id}/download` - 下载转录结果

### 字幕处理
- `POST /api/v1/subtitle` - 创建字幕处理任务
- `GET /api/v1/subtitle/{task_id}` - 查询字幕处理任务状态
- `GET /api/v1/subtitle/{task_id}/download` - 下载字幕处理结果

### 视频合成
- `POST /api/v1/synthesis` - 创建视频合成任务
- `GET /api/v1/synthesis/{task_id}` - 查询视频合成任务状态
- `GET /api/v1/synthesis/{task_id}/download` - 下载合成后的视频

### 视频信息
- `GET /api/v1/video/info?file_path=...` - 获取视频信息

### 批量处理
- `POST /api/v1/batch` - 创建批量处理任务
- `GET /api/v1/batch/{task_id}` - 查询批量处理任务状态

## 项目结构说明

```
.
├── app/                      # FastAPI 应用主目录
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口和路由注册
│   ├── config.py            # 应用配置
│   ├── routers/             # API 路由模块
│   │   ├── __init__.py
│   │   ├── health.py        # 健康检查路由
│   │   ├── transcribe.py    # 转录相关路由
│   │   ├── subtitle.py      # 字幕处理路由
│   │   ├── synthesis.py     # 视频合成路由
│   │   ├── video.py         # 视频信息路由
│   │   └── batch.py         # 批量处理路由
│   ├── schemas/             # Pydantic 数据验证模式
│   │   ├── __init__.py
│   │   ├── common.py        # 通用数据模型（VideoInfo, TaskResponse等）
│   │   ├── transcribe.py    # 转录相关模型
│   │   ├── subtitle.py      # 字幕处理模型
│   │   ├── synthesis.py     # 视频合成模型
│   │   └── batch.py         # 批量处理模型
│   ├── services/            # 业务逻辑服务层
│   │   ├── __init__.py
│   │   ├── task_manager.py  # 任务管理器
│   │   ├── transcribe_service.py    # 转录服务
│   │   ├── subtitle_service.py      # 字幕处理服务
│   │   ├── synthesis_service.py     # 视频合成服务
│   │   ├── video_service.py         # 视频信息服务
│   │   └── batch_service.py         # 批量处理服务
│   └── core/                # 核心业务逻辑（保留原有结构）
│       ├── asr/             # 语音识别模块
│       ├── translate/       # 翻译模块
│       ├── split/           # 字幕分割模块
│       ├── optimize/       # 字幕优化模块
│       ├── tts/             # 文本转语音模块
│       ├── llm/             # 大语言模型模块
│       ├── utils/           # 工具函数
│       ├── entities.py      # 实体定义
│       └── task_factory.py  # 任务工厂
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量配置
└── README.md               # 项目说明文档
```

## 使用示例

### 创建转录任务

```python
import requests

# 创建转录任务
response = requests.post("http://localhost:8000/api/v1/transcribe", json={
    "file_path": "/path/to/video.mp4",
    "config": {
        "transcribe_model": "faster_whisper",
        "transcribe_language": "zh",
        "output_format": "srt"
    }
})

task_id = response.json()["task_id"]

# 查询任务状态
status_response = requests.get(f"http://localhost:8000/api/v1/transcribe/{task_id}")
print(status_response.json())

# 下载结果（任务完成后）
if status_response.json()["status"] == "completed":
    download_response = requests.get(
        f"http://localhost:8000/api/v1/transcribe/{task_id}/download"
    )
    with open("output.srt", "wb") as f:
        f.write(download_response.content)
```

### 创建字幕处理任务

```python
response = requests.post("http://localhost:8000/api/v1/subtitle", json={
    "subtitle_path": "/path/to/subtitle.srt",
    "config": {
        "need_translate": True,
        "translator_service": "openai",
        "target_language": "en",
        "need_optimize": True,
        "need_split": True
    }
})
```

## 开发指南

### 添加新的路由

1. 在 `app/routers/` 目录下创建新的路由文件
2. 使用 `APIRouter` 创建路由实例
3. 在 `app/main.py` 中注册路由

### 添加新的服务

1. 在 `app/services/` 目录下创建新的服务文件
2. 实现业务逻辑，调用 `core` 模块中的功能
3. 在路由中使用服务

### 环境变量配置

使用 `python-dotenv` 管理环境变量：

```bash
uv pip install python-dotenv
```

创建 `.env` 文件：

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
DEBUG=True
```

在代码中使用：

```python
from dotenv import load_dotenv
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")
```

## 测试

### 在 Docker 容器中运行测试（推荐）

项目提供了 Docker Compose 配置来运行测试，确保测试环境与生产环境一致。

#### 使用脚本运行

**Linux/macOS:**
```bash
# 运行字幕接口测试
./scripts/run-tests.sh subtitle

# 运行所有测试
./scripts/run-tests.sh all

# 运行测试并生成覆盖率报告
./scripts/run-tests.sh coverage
```

**Windows (PowerShell):**
```powershell
# 运行字幕接口测试
.\scripts\run-tests.ps1 subtitle

# 运行所有测试
.\scripts\run-tests.ps1 all

# 运行测试并生成覆盖率报告
.\scripts\run-tests.ps1 coverage
```

#### 使用 Makefile

```bash
# 运行字幕接口测试（默认）
make test

# 运行所有测试
make test-all

# 运行测试并生成覆盖率报告
make test-coverage

# 清理测试结果
make clean
```

#### 直接使用 Docker Compose

```bash
# 运行字幕接口测试
docker-compose -f docker-compose.test.yml run --rm test

# 运行所有测试
docker-compose -f docker-compose.test.yml run --rm test-all

# 运行测试并生成覆盖率报告
docker-compose -f docker-compose.test.yml run --rm test-coverage
```

### 本地运行测试（不使用 Docker）

```bash
# 安装测试依赖
uv pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest

# 运行字幕接口测试
pytest tests/test_subtitle.py -v

# 或使用 uv run（无需激活虚拟环境）
uv run pytest tests/test_subtitle.py -v

# 查看测试覆盖率
pytest --cov=app --cov-report=html tests/
```

更多测试说明请参考 [tests/README.md](tests/README.md)

## 部署

### 使用 Docker Compose（推荐）

项目已包含完整的 Docker Compose 配置，可以一键启动：

```bash
# 1. 复制环境变量文件（如果不存在）
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量

# 2. 构建并启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

#### Docker Compose 配置说明

- **端口映射**: `8000:8000` - API 服务端口
- **数据卷挂载**:
  - `./workspace:/app/workspace` - 工作目录（处理中的文件）
  - `./models:/app/models` - 模型目录（AI 模型）
  - `./logs:/app/logs` - 日志目录
  - `./input:/app/input:ro` - 输入文件目录（只读）
  - `./output:/app/output` - 输出文件目录

#### 环境变量配置

创建 `.env` 文件并配置以下变量：

```env
# 应用配置
DEBUG=False
LOG_LEVEL=INFO

# LLM 配置（可选，支持多种环境变量名称）
# 新格式（推荐）
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini

# 兼容旧格式（可选）
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# 翻译服务配置（可选）
DEEPLX_ENDPOINT=http://localhost:1188
```

### 使用 Docker（单独构建）

如果只需要构建单个镜像：

```bash
# 构建镜像
docker build -t video-subtitle-api .

# 运行容器
docker run -d \
  --name video-subtitle-api \
  -p 8000:8000 \
  -v $(pwd)/workspace:/app/workspace \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  video-subtitle-api
```

### GPU 支持

如果系统有 NVIDIA GPU 并安装了 nvidia-docker，可以使用 GPU 版本：

```bash
# 使用 GPU 版本的 Docker Compose
docker-compose -f docker-compose.gpu.yml up -d

# 或者单独构建 GPU 镜像
docker build -f Dockerfile.gpu -t video-subtitle-api-gpu .
docker run -d \
  --name video-subtitle-api-gpu \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/workspace:/app/workspace \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  video-subtitle-api-gpu
```

**注意**: GPU 版本需要：
- NVIDIA GPU 驱动
- nvidia-docker2 或 Docker with GPU support
- CUDA 12.1+ 运行时

## 常用命令

### 开发环境

```bash
# 启动开发服务器
uvicorn app.main:app --reload
# 或使用 uv run（无需激活虚拟环境）
uv run uvicorn app.main:app --reload

# 检查代码格式（需要 black）
uv pip install black
uv run black app/

# 类型检查（需要 mypy）
uv pip install mypy
uv run mypy app/
```

### Docker Compose 命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec api bash
```

## 学习资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [FastAPI 中文文档](https://fastapi.tiangolo.com/zh/)
- [Pydantic 文档](https://docs.pydantic.dev/)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

