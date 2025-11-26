# AI Subtitle Learner

<div align="center">

**An AI-powered subtitle learning system for language learning with YouTube videos**

[中文](README.zh-CN.md) | [English](README.md)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a98f?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-000000?style=flat-square&logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776ab?style=flat-square&logo=python)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178c6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=flat-square&logo=docker)](https://www.docker.com/)

</div>

## 📖 Overview

AI Subtitle Learner is a complete language learning system that helps you learn languages (especially Japanese) through YouTube videos. It automatically downloads videos, transcribes audio with precise timestamps, processes subtitles, provides translations, and offers an interactive learning experience.

### Key Features

- 🎬 **YouTube Video Processing**: Download audio from YouTube videos and automatically transcribe
- 🎯 **Precise Timestamps**: Uses WhisperX for accurate word-level timestamps
- 🌐 **AI-Powered Translation**: LLM-based translation with customizable prompts
- 📚 **Interactive Dictionary**: Right-click words to query definitions powered by LLM
- 🎨 **Modern Web UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- 🔄 **Async Task Processing**: Celery + RabbitMQ for scalable background processing
- 💾 **Smart Caching**: Redis caching for ASR and translation results to reduce costs
- 📦 **Object Storage**: MinIO (S3-compatible) for file storage
- 🗄️ **Persistent Storage**: PostgreSQL for task state and metadata

## 📸 Screenshots

### Main Interface
The main interface shows the video player with synchronized subtitles, allowing you to learn languages through YouTube videos with real-time subtitle highlighting.

![Main Interface](screenshots/Screenshot1.png)

*Figure 1: Main interface showing video playback with synchronized subtitles and translation*

### Dictionary Feature
Right-click on any word in the subtitles to instantly query its definition, pronunciation, and usage examples powered by LLM.

![Dictionary Feature](screenshots/Screenshot2.png)

*Figure 2: Interactive dictionary feature - right-click on words to query definitions*

## 🏗️ Architecture

### Production-Ready Design

- **Message Queue**: RabbitMQ for task distribution
- **Distributed Tasks**: Celery workers for horizontal scaling
- **High Availability**: Task persistence, retry mechanisms, dead letter queues
- **Object Storage**: MinIO (S3-compatible) for large files
- **Async Processing**: API layer separated from worker layer

### System Components

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   FastAPI   │────▶│  RabbitMQ   │────▶│   Celery     │
│   (API)     │     │  (Broker)   │     │  (Worker)    │
│             │     │             │     │              │
│  - Receive  │     │  - Task     │     │  - Download  │
│    Requests │     │    Queue    │     │    Video     │
│  - Create   │     │  - Message  │     │  - Transcribe│
│    Tasks    │     │    Routing  │     │  - Process   │
└─────────────┘     └─────────────┘     └──────────────┘
      │                    │                    │
      │                    │                    │
      ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│ PostgreSQL  │     │    Redis    │     │    MinIO     │
│ (Database)  │     │   (Cache)   │     │  (Storage)   │
│             │     │             │     │              │
│ - Task      │     │ - ASR Cache │     │ - Audio      │
│   State     │     │ - Translation│    │   Files      │
│ - Metadata  │     │   Cache     │     │ - Subtitles  │
└─────────────┘     └─────────────┘     └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.12+ and Node.js 18+ for local development

### Using Docker Compose (Recommended)

The easiest way to get started:

```bash
# 1. Clone the repository
git clone <repository-url>
cd AI-Subtitle-Learner

# 2. Create environment file
cp .env.example .env
# Edit .env file with your configuration (see Configuration section)

# 3. Start all services
docker-compose up -d

# 4. Check service status
docker-compose ps

# 5. View logs
docker-compose logs -f
```

After starting, access:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### Local Development

#### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use uv (recommended, faster)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -r requirements.txt

# Install frontend dependencies
cd web
npm install
```

#### 2. Start Infrastructure Services

```bash
# Start infrastructure only (database, Redis, RabbitMQ, MinIO)
docker-compose up -d postgres redis rabbitmq minio
```

#### 3. Configure Environment Variables

Create a `.env` file:

```env
# Application
DEBUG=False
LOG_LEVEL=INFO
WORK_DIR=./workspace
MODEL_DIR=./models
LOG_DIR=./logs

# Database
DATABASE_URL=postgresql://subtitle:subtitle@localhost:5432/subtitle

# Redis
REDIS_URL=redis://localhost:6379/0

# RabbitMQ
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=subtitle-files

# LLM (optional, supports multiple env var names)
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o-mini
```

#### 4. Initialize Database

```bash
python -m app.database.init_db
```

#### 5. Start Services

```bash
# Terminal 1: Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery worker
celery -A app.celery worker --loglevel=info --concurrency=2 --max-tasks-per-child=10 -Q default,video,transcribe,subtitle

# Terminal 3: Start frontend (optional)
cd web
npm run dev
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **Python 3.12**: Programming language
- **Celery**: Distributed task queue
- **RabbitMQ**: Message broker
- **PostgreSQL**: Relational database
- **Redis**: Cache and result backend
- **MinIO**: S3-compatible object storage
- **WhisperX**: Speech recognition with word-level timestamps
- **LLM**: Large language models for translation and dictionary

### Frontend
- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: UI component library
- **i18next**: Internationalization
- **React Player**: Video player component

## 📋 API Endpoints

### Health Check
- `GET /health` - Health check endpoint

### Video Analysis
- `POST /api/v1/video/analyze?url=...` - Start video analysis task (download audio and transcribe)
- `GET /api/v1/video/analyze/{task_id}` - Get video analysis task status

### Subtitle Processing
- `GET /api/v1/subtitle/{task_id}/content` - Get subtitle content (JSON format with timestamps)

### Dictionary
- `POST /api/v1/dictionary/query` - Query word definitions (LLM-powered)

## 📁 Project Structure

```
.
├── app/                      # FastAPI application (backend)
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration
│   ├── celery/              # Celery application & tasks
│   ├── routers/             # API routes (health, video, subtitle, dictionary)
│   ├── services/            # High-level service layer (task manager, dictionary)
│   ├── database/            # DB models, session and initialization
│   └── core/                # Core domain logic
│       ├── asr/             # Speech recognition (WhisperX integration)
│       ├── translate/       # Translation pipeline
│       ├── split/           # Subtitle segmentation
│       ├── analyze/         # Text / Japanese analysis
│       ├── llm/             # LLM abstraction & prompts
│       ├── storage/         # Storage abstraction (MinIO, workspace, cache)
│       └── utils/           # Utility helpers
├── web/                      # Next.js frontend
│   ├── app/                 # Next.js app router
│   ├── components/          # React components (video, subtitles, dictionary, etc.)
│   ├── lib/                 # Frontend utilities & API helpers
│   └── locales/             # i18n translation files
├── nginx/                    # Nginx reverse proxy config
│   ├── nginx.conf           # Main Nginx config
│   └── README.md            # Nginx usage & routes
├── models/                   # Local WhisperX and related models
├── workspace/                # Input/output workspace and caches
├── scripts/                  # Helper scripts (model download, test runner, etc.)
├── tests/                    # Backend API tests
├── docker-compose.yml        # Default Docker Compose
├── docker-compose.gpu.yml    # GPU-enabled Compose (WhisperX on GPU)
├── docker-compose.test.yml   # Testing Compose (CI / local test env)
├── docker-compose.override.example.yml # Example override for customization
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Python project metadata / tooling
├── run.sh                    # Helper script to start services
└── README.md                 # This file
```

## 🔧 Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# RabbitMQ
CELERY_BROKER_URL=amqp://user:password@host:5672//
CELERY_RESULT_BACKEND=redis://host:6379/1

# MinIO
MINIO_ENDPOINT=host:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=subtitle-files
```

### Optional Environment Variables

```env
# LLM Configuration
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o-mini

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
WORK_DIR=./workspace
MODEL_DIR=./models
LOG_DIR=./logs
```

## 📖 Usage Examples

### 1. Start Video Analysis

```python
import requests

# Start analysis task
response = requests.post(
    "http://localhost:8000/api/v1/video/analyze",
    params={"url": "https://www.youtube.com/watch?v=..."}
)

task_id = response.json()["task_id"]
print(f"Task created: {task_id}")

# Check task status
status_response = requests.get(
    f"http://localhost:8000/api/v1/video/analyze/{task_id}"
)
print(status_response.json())

# Get subtitle content (after completion)
if status_response.json()["status"] == "completed":
    subtitle_task_id = status_response.json()["subtitle_task"]["task_id"]
    content_response = requests.get(
        f"http://localhost:8000/api/v1/subtitle/{subtitle_task_id}/content"
    )
    subtitle_data = content_response.json()
    print(subtitle_data)
```

### 2. Query Dictionary

```python
# Query word definition
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

## 🧪 Testing

### Using Docker Compose

```bash
# Run all tests
docker-compose -f docker-compose.test.yml run --rm test

# Run tests with coverage
docker-compose -f docker-compose.test.yml run --rm test-coverage
```

### Local Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# View coverage
pytest --cov=app --cov-report=html
```

## 🚢 Deployment

### Production Deployment

1. **Configure environment variables** for production
2. **Start services**:
```bash
docker-compose up -d
   ```
3. **Scale workers**:
   ```bash
   docker-compose up -d --scale worker=3
   ```

### Cloud Storage Migration

MinIO supports S3-compatible API, easy migration to cloud storage:

```env
# AWS S3
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=your-aws-access-key
MINIO_SECRET_KEY=your-aws-secret-key
MINIO_SECURE=true

# Alibaba Cloud OSS
MINIO_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
MINIO_ACCESS_KEY=your-oss-access-key
MINIO_SECRET_KEY=your-oss-secret-key
MINIO_SECURE=true
```

## 📝 Common Commands

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Stop services
docker-compose down

# Rebuild images
docker-compose build --no-cache

# Scale workers
docker-compose up -d --scale worker=3
```

### Celery Management

```bash
# View active tasks
celery -A app.celery inspect active

# View registered tasks
celery -A app.celery inspect registered

# View worker stats
celery -A app.celery inspect stats

# View task result
celery -A app.celery result <task_id>
```

## 🐛 Troubleshooting

### Tasks Not Executing

1. Check if RabbitMQ is running
2. Check if Worker is started: `docker-compose ps worker`
3. View Worker logs: `docker-compose logs worker`

### File Upload Failed

1. Check if MinIO is running
2. Check MinIO connection configuration
3. Verify bucket exists in MinIO console

### Database Connection Failed

1. Check if PostgreSQL is running
2. Check database connection string
3. Verify database is initialized

## 📚 Documentation

- **Nginx reverse proxy & routes**: `nginx/README.md`
- **Backend API tests overview**: `tests/README.md`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 🙏 Acknowledgments

- [WhisperX](https://github.com/m-bain/whisperX) for speech recognition
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Next.js](https://nextjs.org/) for the frontend framework
