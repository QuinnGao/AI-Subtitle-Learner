# AI Subtitle Learner (AI字幕学习助手)

这是一个完整的AI字幕语言学习系统，包含基于 FastAPI 的后端服务和基于 Next.js 的前端应用。支持从 YouTube 下载视频、自动转录、字幕处理、翻译和交互式学习等功能。

## 🏗️ 架构特点

- **生产级架构**：采用消息队列、分布式任务调度、数据库持久化
- **可扩展设计**：支持多 Worker 节点、水平扩展
- **高可用性**：任务持久化、失败重试、死信队列
- **对象存储**：使用 MinIO（S3 兼容）存储文件
- **异步处理**：API 层与 Worker 层分离，不阻塞请求

## 技术栈

### 后端核心
- **FastAPI**: 现代、快速的 Web 框架，用于构建 API
- **Python 3.12**: 编程语言
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证和设置管理

### 消息队列与任务调度
- **Celery**: 分布式任务队列
- **RabbitMQ**: 消息代理（Broker）
- **Redis**: 任务结果后端和缓存

### 数据存储
- **PostgreSQL**: 任务状态和元数据持久化
- **MinIO**: 对象存储（S3 兼容），存储视频、音频、字幕文件
- **Redis**: 计算结果缓存（ASR、翻译等）

### AI 模型
- **WhisperX**: 语音识别模型（精准时间戳）
- **LLM**: 大语言模型（用于翻译和字典查询）

### 前端
- **Next.js 14**: React 框架
- **TypeScript**: 类型安全
- **Tailwind CSS**: 样式框架
- **shadcn/ui**: UI 组件库
- **i18next**: 国际化
- **React Player**: 视频播放器

## 项目特性

### 后端（FastAPI）
- 🚀 **高性能异步 API**：基于 FastAPI 和 Uvicorn
- 📝 **自动生成 API 文档**：Swagger UI 和 ReDoc
- 🔒 **类型提示和数据验证**：Pydantic 模式验证
- 🎬 **视频下载与转录**：从 YouTube 下载音频并自动转录
- 🌐 **字幕翻译**：支持 LLM 大模型翻译（OpenAI 兼容 API）
- ✂️ **字幕处理**：自动分割、日语分析、翻译
- 📚 **字典查询**：基于 LLM 的单词查询功能
- 🔄 **异步任务处理**：Celery + RabbitMQ，支持任务队列和进度查询
- 💾 **智能缓存**：Redis 缓存 ASR 结果、翻译结果，节省成本
- 🗄️ **数据持久化**：PostgreSQL 存储任务状态，服务重启不丢失
- 📦 **对象存储**：MinIO 存储大文件，支持分布式部署

### 前端（Next.js）
- 🎨 **现代化 UI**：基于 Tailwind CSS 和 shadcn/ui
- 🎬 **视频播放器**：集成 React Player，支持播放控制
- 📝 **交互式字幕**：实时高亮当前播放位置，点击跳转
- 📚 **字典查询**：右键点击单词查询释义（支持响应式布局）
- 🌐 **国际化**：支持中文/英文切换
- 📱 **响应式设计**：适配桌面和移动设备

## 快速开始

### 方式 1：使用 Docker Compose（推荐）

这是最简单的方式，一键启动所有服务：

```bash
# 1. 克隆项目
git clone <repository-url>
cd AI-Subtitle-Learner

# 2. 创建环境变量文件
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量（见下方配置说明）

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

服务启动后，访问：
- **后端 API 文档**：http://localhost:8000/docs
- **前端界面**：http://localhost:3000
- **RabbitMQ 管理界面**：http://localhost:15672（guest/guest）
- **MinIO 控制台**：http://localhost:9001（minioadmin/minioadmin）

### 方式 2：本地开发环境

#### 1. 环境要求

- Python 3.12+
- Node.js 18+（前端开发）
- PostgreSQL 15+（或使用 Docker）
- Redis 7+（或使用 Docker）
- RabbitMQ 3+（或使用 Docker）
- MinIO（或使用 Docker）

#### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 或使用 uv（推荐，速度更快）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -r requirements.txt
```

#### 3. 启动基础设施服务

使用 Docker Compose 启动基础设施：

```bash
# 只启动基础设施服务（数据库、Redis、RabbitMQ、MinIO）
docker-compose up -d postgres redis rabbitmq minio
```

#### 4. 配置环境变量

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

# 兼容旧格式（可选）
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
```

#### 5. 初始化数据库

```bash
# 初始化数据库表
python -m app.database.init_db
```

#### 6. 启动 API 服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 uv run
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 7. 启动 Celery Worker

```bash
# 启动 Worker（处理异步任务）
celery -A app.celery worker --loglevel=info --concurrency=2 --max-tasks-per-child=10 -Q default,video,transcribe,subtitle

# 或使用 uv run
uv run celery -A app.celery worker --loglevel=info --concurrency=2 --max-tasks-per-child=10 -Q default,video,transcribe,subtitle
```

#### 8. 启动前端服务（可选）

```bash
cd web
npm install
npm run dev
```

## 系统架构

### 服务组件

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

### 任务流程

1. **API 接收请求** → 创建任务记录（PostgreSQL）
2. **发送任务到队列** → RabbitMQ（按任务类型路由到不同队列）
3. **Worker 处理任务** → Celery Worker 从队列获取任务
   - `video` 队列：视频下载任务
   - `transcribe` 队列：音频转录任务
   - `subtitle` 队列：字幕处理任务
4. **存储文件** → MinIO 对象存储（音频、字幕、处理结果）
5. **缓存结果** → Redis 缓存计算结果（ASR、翻译、字典查询）
6. **更新任务状态** → PostgreSQL（任务状态、进度、关联关系）

### 数据流

```
用户请求
  ↓
FastAPI (创建任务)
  ↓
RabbitMQ (任务队列)
  ↓
Celery Worker (处理任务)
  ├─→ 下载视频 → MinIO
  ├─→ 转录音频 → MinIO + Redis 缓存
  ├─→ 处理字幕 → MinIO + Redis 缓存
  └─→ 更新任务状态 → PostgreSQL
```

## Docker Compose 服务说明

项目包含以下 Docker 服务：

- **api**: FastAPI 应用服务（端口 8000）
- **worker**: Celery Worker 进程（处理异步任务）
- **web**: Next.js 前端应用（端口 3000）
- **postgres**: PostgreSQL 数据库（端口 5432）
- **redis**: Redis 缓存（端口 6379）
- **rabbitmq**: RabbitMQ 消息队列（端口 5672, 管理界面 15672）
- **minio**: MinIO 对象存储（端口 9000, 控制台 9001）

### 服务依赖关系

```
api ──┐
      ├──→ postgres
      ├──→ redis
      ├──→ rabbitmq
      └──→ minio

worker ──┐
        ├──→ postgres
        ├──→ redis
        ├──→ rabbitmq
        └──→ minio

web ──→ api
```

## API 端点

### 健康检查
- `GET /health` - 健康检查

### 视频分析
- `POST /api/v1/video/analyze?url=...` - 从 YouTube URL 开始分析任务（下载音频并转录）
- `GET /api/v1/video/analyze/{task_id}` - 查询视频分析任务状态

### 字幕处理
- `GET /api/v1/subtitle/{task_id}/content` - 获取字幕内容（JSON 格式，包含时间戳）

### 字典查询
- `POST /api/v1/dictionary/query` - 查询单词释义（基于 LLM）

## 项目结构

```
.
├── app/                      # FastAPI 应用主目录
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 应用配置
│   ├── celery/              # Celery 应用模块
│   │   ├── __init__.py      # Celery 模块导出
│   │   ├── app.py           # Celery 应用配置
│   │   ├── tasks/           # Celery 任务定义
│   │   │   ├── __init__.py
│   │   │   ├── video_tasks.py      # 视频下载任务
│   │   │   ├── transcribe_tasks.py # 转录任务
│   │   │   └── subtitle_tasks.py   # 字幕处理任务
│   │   └── services/       # Celery 任务使用的服务层
│   │       ├── __init__.py
│   │       ├── video_download_service.py
│   │       ├── transcribe_service.py
│   │       └── subtitle_service.py
│   ├── routers/             # API 路由模块
│   │   ├── health.py        # 健康检查路由
│   │   ├── video.py         # 视频分析路由
│   │   ├── subtitle.py      # 字幕处理路由
│   │   └── dictionary.py    # 字典查询路由
│   ├── services/            # 业务逻辑服务层
│   │   ├── task_manager.py  # 任务管理器（数据库持久化）
│   │   └── dictionary_service.py
│   ├── database/            # 数据库模块
│   │   ├── models.py        # SQLAlchemy 模型
│   │   ├── base.py          # 数据库配置
│   │   └── init_db.py       # 数据库初始化
│   ├── core/                # 核心业务逻辑
│   │   ├── asr/             # 语音识别模块
│   │   ├── translate/       # 翻译模块
│   │   ├── split/           # 字幕分割模块
│   │   ├── analyze/         # 文本分析模块
│   │   ├── llm/             # 大语言模型模块
│   │   ├── storage/         # 存储模块
│   │   │   ├── __init__.py
│   │   │   ├── minio_storage.py  # MinIO 存储服务
│   │   │   └── init_minio.py     # MinIO 初始化
│   │   └── utils/           # 工具函数
│   └── schemas/             # Pydantic 数据验证模式
├── web/                      # Next.js 前端应用
├── docker-compose.yml       # Docker Compose 配置
├── requirements.txt         # Python 依赖
└── README.md                # 项目说明文档
```

## 环境变量配置

### 必需配置

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

### 可选配置

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

## 使用示例

### 1. 从 YouTube URL 开始分析

```python
import requests

# 开始分析任务（下载音频并转录）
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

## 开发指南

### 添加新的 Celery 任务

1. 在 `app/celery/tasks/` 目录下创建新的任务文件
2. 在 `app/celery/services/` 目录下创建对应的服务文件（业务逻辑）
3. 使用 `@celery_app.task` 装饰器定义任务
4. 在路由中调用 `task.delay()` 发送任务到队列

示例：

```python
# app/celery/tasks/my_tasks.py
from app.celery import celery_app
from app.celery.services.my_service import MyService

my_service = MyService()

@celery_app.task(bind=True, name="my_task", max_retries=3)
def my_task(self, task_id: str, data: dict):
    """Celery 任务：执行业务逻辑"""
    try:
        my_service.process_task(task_id, data)
    except Exception as e:
        # 任务失败时重试
        raise self.retry(exc=e, countdown=60)
```

### 添加新的路由

1. 在 `app/routers/` 目录下创建新的路由文件
2. 使用 `APIRouter` 创建路由实例
3. 在 `app/main.py` 中注册路由

### 数据库迁移

使用 Alembic 进行数据库迁移：

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head
```

## 测试

### 使用 Docker Compose 运行测试

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

## 部署

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

4. **监控服务**：
   - 查看日志：`docker-compose logs -f`
   - 查看任务状态：RabbitMQ 管理界面
   - 查看存储：MinIO 控制台

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

## 常用命令

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

## 监控与运维

### 健康检查

- API 健康检查：`GET http://localhost:8000/health`
- RabbitMQ 管理界面：http://localhost:15672
- MinIO 控制台：http://localhost:9001

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f worker

# 查看最近 100 行日志
docker-compose logs --tail=100 api
```

## 故障排查

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

## 文档

- [架构设计文档](docs/ARCHITECTURE.md)
- [存储架构文档](docs/STORAGE.md)
- [日志配置文档](docs/LOGGING.md)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
