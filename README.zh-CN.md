# AI Subtitle Learner (AI日语字幕学习助手)

<div align="center">

**基于 AI 的 YouTube 视频字幕语言学习系统**

[中文](README.zh-CN.md) | [English](README.md)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a98f?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-000000?style=flat-square&logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776ab?style=flat-square&logo=python)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178c6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=flat-square&logo=docker)](https://www.docker.com/)

</div>

## 📖 项目简介

AI Subtitle Learner 是一个完整的语言学习系统，帮助您通过 YouTube 视频学习语言（特别是日语）。它能够自动下载视频、使用精确时间戳转录音频、处理字幕、提供翻译，并提供交互式学习体验。

### 核心特性

- 🎬 **YouTube 视频处理**：从 YouTube 视频下载音频并自动转录
- 🎯 **精确时间戳**：使用 WhisperX 提供单词级别的精确时间戳
- 🌐 **AI 翻译**：基于大语言模型的翻译，支持自定义提示词
- 📚 **交互式字典**：右键点击单词查询释义，基于 LLM 驱动
- 🎨 **现代化 Web UI**：基于 Next.js 和 Tailwind CSS 构建的响应式界面
- 🔄 **异步任务处理**：Celery + RabbitMQ 实现可扩展的后台处理
- 💾 **智能缓存**：Redis 缓存 ASR 和翻译结果，降低成本
- 📦 **对象存储**：MinIO（S3 兼容）用于文件存储
- 🗄️ **持久化存储**：PostgreSQL 存储任务状态和元数据

## 📸 运行截图

### 主界面
主界面显示视频播放器与同步字幕，让您通过 YouTube 视频学习语言，实时高亮显示当前播放位置的字幕。

![主界面](screenshots/Screenshot1.png)

*图 1：主界面展示视频播放、同步字幕和翻译功能*

### 字典功能
在字幕中右键点击任意单词，即可立即查询其释义、发音和使用示例，由 LLM 驱动。

![字典功能](screenshots/Screenshot2.png)

*图 2：交互式字典功能 - 右键点击单词查询释义*

## 🏗️ 系统架构

### 生产级设计

- **消息队列**：RabbitMQ 用于任务分发
- **分布式任务**：Celery workers 支持水平扩展
- **高可用性**：任务持久化、重试机制、死信队列
- **对象存储**：MinIO（S3 兼容）存储大文件
- **异步处理**：API 层与 Worker 层分离

### 系统组件

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  RabbitMQ   │────▶│   Celery    │
│   (API)     │     │  (Broker)   │     │  (Worker)   │
│             │     │             │     │             │
│  - 接收请求  │     │  - 任务队列  │     │  - 下载视频  │
│  - 创建任务  │     │  - 消息分发  │     │  - 转录音频  │
│  - 查询状态  │     │             │     │  - 处理字幕  │
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │
      │                    │                    │
      ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ PostgreSQL  │     │    Redis    │     │    MinIO    │
│ (数据库)     │     │   (缓存)    │     │  (对象存储)  │
│             │     │             │     │             │
│ - 任务状态   │     │ - ASR缓存   │     │ - 音频文件   │
│ - 任务关系   │     │ - 翻译缓存  │     │ - 字幕文件   │
│ - 元数据     │     │ - 结果后端  │     │ - 处理结果   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- （可选）Python 3.12+ 和 Node.js 18+（用于本地开发）

### 使用 Docker Compose（推荐）

最简单的启动方式：

```bash
# 1. 克隆项目
git clone <repository-url>
cd AI-Subtitle-Learner

# 2. 创建环境变量文件
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量（见配置说明）

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

启动后访问：
- **前端界面**：http://localhost:3000
- **后端 API 文档**：http://localhost:8000/docs
- **RabbitMQ 管理界面**：http://localhost:15672（guest/guest）
- **MinIO 控制台**：http://localhost:9001（minioadmin/minioadmin）

### 本地开发环境

#### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 或使用 uv（推荐，速度更快）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -r requirements.txt

# 安装前端依赖
cd web
npm install
```

#### 2. 启动基础设施服务

```bash
# 只启动基础设施服务（数据库、Redis、RabbitMQ、MinIO）
docker-compose up -d postgres redis rabbitmq minio
```

#### 3. 配置环境变量

创建 `.env` 文件：

```env
# 应用配置
DEBUG=False
LOG_LEVEL=INFO
WORK_DIR=./workspace
MODEL_DIR=./models
LOG_DIR=./logs

# 数据库配置
DATABASE_URL=postgresql://subtitle:subtitle@localhost:5432/subtitle

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# RabbitMQ 配置
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=subtitle-files

# LLM 配置（可选，支持多种环境变量名称）
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o-mini
```

#### 4. 初始化数据库

```bash
python -m app.database.init_db
```

#### 5. 启动服务

```bash
# 终端 1：启动 API 服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2：启动 Celery Worker
celery -A app.celery worker --loglevel=info --concurrency=2 --max-tasks-per-child=10 -Q default,video,transcribe,subtitle

# 终端 3：启动前端（可选）
cd web
npm run dev
```

## 🛠️ 技术栈

### 后端
- **FastAPI**：现代、快速的 Web 框架
- **Python 3.12**：编程语言
- **Celery**：分布式任务队列
- **RabbitMQ**：消息代理
- **PostgreSQL**：关系型数据库
- **Redis**：缓存和结果后端
- **MinIO**：S3 兼容的对象存储
- **WhisperX**：带单词级时间戳的语音识别
- **LLM**：用于翻译和字典查询的大语言模型

### 前端
- **Next.js 14**：React 框架
- **TypeScript**：类型安全
- **Tailwind CSS**：实用优先的 CSS 框架
- **shadcn/ui**：UI 组件库
- **i18next**：国际化
- **React Player**：视频播放器组件

## 📋 API 端点

### 健康检查
- `GET /health` - 健康检查端点

### 视频分析
- `POST /api/v1/video/analyze?url=...` - 开始视频分析任务（下载音频并转录）
- `GET /api/v1/video/analyze/{task_id}` - 获取视频分析任务状态

### 字幕处理
- `GET /api/v1/subtitle/{task_id}/content` - 获取字幕内容（JSON 格式，包含时间戳）

### 字典查询
- `POST /api/v1/dictionary/query` - 查询单词释义（基于 LLM）

## 📁 项目结构

```
.
├── app/                      # FastAPI 应用主目录
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 应用配置
│   ├── celery/              # Celery 应用模块
│   │   ├── app.py           # Celery 应用配置
│   │   ├── tasks/           # Celery 任务定义
│   │   └── services/        # Celery 任务使用的服务层
│   ├── routers/             # API 路由模块
│   ├── services/            # 业务逻辑服务层
│   ├── database/            # 数据库模块
│   └── core/                # 核心业务逻辑
│       ├── asr/             # 语音识别模块
│       ├── translate/       # 翻译模块
│       ├── split/           # 字幕分割模块
│       ├── analyze/         # 文本分析模块
│       ├── llm/             # 大语言模型模块
│       └── storage/         # 存储模块
├── web/                      # Next.js 前端应用
│   ├── app/                 # Next.js app 目录
│   ├── components/          # React 组件
│   ├── lib/                 # 工具函数
│   └── locales/             # i18n 翻译文件
├── docker-compose.yml       # Docker Compose 配置
├── requirements.txt         # Python 依赖
├── screenshots/             # 应用运行截图
│   ├── Screenshot1.png     # 主界面截图
│   └── Screenshot2.png     # 字典功能截图
└── README.md                # 项目说明文档
```

## 🔧 配置说明

### 必需的环境变量

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis 配置
REDIS_URL=redis://host:6379/0

# RabbitMQ 配置
CELERY_BROKER_URL=amqp://user:password@host:5672//
CELERY_RESULT_BACKEND=redis://host:6379/1

# MinIO 配置
MINIO_ENDPOINT=host:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=subtitle-files
```

### 可选的环境变量

```env
# LLM 配置（用于翻译和字典查询）
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o-mini

# 应用配置
DEBUG=False
LOG_LEVEL=INFO
WORK_DIR=./workspace
MODEL_DIR=./models
LOG_DIR=./logs
```

## 📖 使用示例

### 1. 开始视频分析

```python
import requests

# 开始分析任务
response = requests.post(
    "http://localhost:8000/api/v1/video/analyze",
    params={"url": "https://www.youtube.com/watch?v=..."}
)

task_id = response.json()["task_id"]
print(f"任务已创建: {task_id}")

# 查询任务状态
status_response = requests.get(
    f"http://localhost:8000/api/v1/video/analyze/{task_id}"
)
print(status_response.json())

# 获取字幕内容（任务完成后）
if status_response.json()["status"] == "completed":
    subtitle_task_id = status_response.json()["subtitle_task"]["task_id"]
    content_response = requests.get(
        f"http://localhost:8000/api/v1/subtitle/{subtitle_task_id}/content"
    )
    subtitle_data = content_response.json()
    print(subtitle_data)
```

### 2. 查询字典

```python
# 查询单词释义
response = requests.post(
    "http://localhost:8000/api/v1/dictionary/query",
    json={
        "word": "こんにちは",
        "furigana": "こんにちは",
        "part_of_speech": "感叹词"
    }
)
print(response.json())
```

## 🧪 测试

### 使用 Docker Compose

```bash
# 运行所有测试
docker-compose -f docker-compose.test.yml run --rm test

# 运行测试并生成覆盖率报告
docker-compose -f docker-compose.test.yml run --rm test-coverage
```

### 本地运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行测试
pytest

# 查看覆盖率
pytest --cov=app --cov-report=html
```

## 🚢 部署

### 生产环境部署

1. **配置环境变量**：设置生产环境的数据库、Redis、RabbitMQ、MinIO 连接信息

2. **启动服务**：
   ```bash
   docker-compose up -d
   ```

3. **扩展 Worker**：可以启动多个 Worker 节点处理任务
   ```bash
   docker-compose up -d --scale worker=3
   ```

### 云存储迁移

MinIO 支持 S3 兼容 API，可以轻松迁移到云存储：

```env
# AWS S3
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=your-aws-access-key
MINIO_SECRET_KEY=your-aws-secret-key
MINIO_SECURE=true

# 阿里云 OSS
MINIO_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
MINIO_ACCESS_KEY=your-oss-access-key
MINIO_SECRET_KEY=your-oss-secret-key
MINIO_SECURE=true
```

## 📝 常用命令

### Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
docker-compose logs -f worker

# 停止服务
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 扩展 Worker 节点
docker-compose up -d --scale worker=3
```

### Celery 管理

```bash
# 查看任务状态
celery -A app.celery inspect active

# 查看注册的任务
celery -A app.celery inspect registered

# 查看 Worker 状态
celery -A app.celery inspect stats

# 查看任务结果
celery -A app.celery result <task_id>
```

## 🐛 故障排查

### 任务不执行

1. 检查 RabbitMQ 是否正常运行
2. 检查 Worker 是否启动：`docker-compose ps worker`
3. 查看 Worker 日志：`docker-compose logs worker`

### 文件上传失败

1. 检查 MinIO 是否正常运行
2. 检查 MinIO 连接配置
3. 查看 MinIO 控制台确认存储桶存在

### 数据库连接失败

1. 检查 PostgreSQL 是否正常运行
2. 检查数据库连接字符串
3. 确认数据库已初始化

## 📚 文档

- [架构设计文档](docs/ARCHITECTURE.md)
- [存储架构文档](docs/STORAGE.md)
- [日志配置文档](docs/LOGGING.md)
- [K8S 决策文档](docs/K8S_DECISION.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [WhisperX](https://github.com/m-bain/whisperX) - 语音识别
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Next.js](https://nextjs.org/) - 前端框架

