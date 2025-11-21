# 日志使用说明

## 日志配置

项目使用 **loguru** 进行日志记录。loguru 是一个功能强大、易于使用的 Python 日志库，具有以下特点：

- 🎨 **彩色输出**：终端中自动彩色显示（Docker 中也可查看）
- 📝 **自动格式化**：无需手动配置格式
- 🔄 **自动轮转**：自动管理日志文件大小和保留时间
- 🚀 **高性能**：异步写入，性能优异
- 🐛 **更好的调试**：自动记录堆栈跟踪和上下文信息

日志会同时输出到：
- **控制台**（标准错误输出）：可以在 Docker 容器日志中查看，带彩色格式
- **日志文件**：保存在 `logs/app.log` 目录，自动轮转和压缩

## 日志级别

支持以下日志级别（从低到高）：
- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

## 在 Docker 中查看日志

### 方法 1：使用 docker logs 命令

```bash
# 查看实时日志（推荐）
docker logs -f video-subtitle-api

# 查看最近 100 行日志
docker logs --tail 100 video-subtitle-api

# 查看指定时间范围的日志
docker logs --since 1h video-subtitle-api

# 查看带时间戳的日志
docker logs -t video-subtitle-api

# 只查看字幕相关日志
docker logs video-subtitle-api 2>&1 | grep "subtitle"

# 只查看错误日志
docker logs video-subtitle-api 2>&1 | grep "ERROR"
```

### 方法 2：使用 docker-compose logs

```bash
# 查看实时日志
docker-compose logs -f api

# 查看最近 100 行日志
docker-compose logs --tail 100 api

# 查看所有服务的日志
docker-compose logs -f
```

### 方法 3：查看日志文件

日志文件保存在挂载的 `./logs` 目录中：

```bash
# 查看日志文件（实时）
tail -f logs/app.log

# 查看最近 100 行
tail -n 100 logs/app.log

# 搜索特定内容
grep "任务" logs/app.log

# 搜索错误日志
grep "ERROR" logs/app.log

# 查看特定任务的日志
grep "任务 abc123" logs/app.log
```

## 日志格式

### 控制台输出格式（带颜色）

```
2025-11-16 19:00:00 | INFO     | subtitle_service:process_subtitle_task:35 | [任务 abc123] 开始处理字幕任务
2025-11-16 19:00:01 | INFO     | subtitle_service:process_subtitle_task:62 | [任务 abc123] 字幕加载完成，共 100 条字幕
2025-11-16 19:00:02 | ERROR    | subtitle_service:process_subtitle_task:224 | [任务 abc123] 字幕处理失败: 文件不存在
```

### 文件输出格式（详细格式，带毫秒）

```
2025-11-16 19:00:00.123 | INFO     | subtitle_service:process_subtitle_task:35 | [任务 abc123] 开始处理字幕任务
2025-11-16 19:00:01.456 | INFO     | subtitle_service:process_subtitle_task:62 | [任务 abc123] 字幕加载完成，共 100 条字幕
2025-11-16 19:00:02.789 | ERROR    | subtitle_service:process_subtitle_task:224 | [任务 abc123] 字幕处理失败: 文件不存在
```

### 日志字段说明

- `time`: 时间戳（控制台精确到秒，文件精确到毫秒）
- `level`: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `name`: 日志记录器名称（如 subtitle_service, subtitle_router）
- `function`: 函数名
- `line`: 代码行号
- `message`: 日志消息

## 日志内容

### 字幕处理服务日志

字幕处理服务 (`subtitle_service`) 会记录以下信息：

- **任务开始**: 任务 ID、请求参数
- **文件验证**: 字幕文件路径、验证结果
- **配置信息**: 翻译、优化、分割等配置
- **处理步骤**: 
  - 字幕加载（字幕数量）
  - 分割处理
  - LLM 配置验证
  - 断句处理
  - 优化处理（进度）
  - 翻译处理（进度、翻译服务）
  - 结果保存（输出路径）
- **错误信息**: 详细的错误堆栈和上下文

### 路由日志

字幕路由 (`subtitle_router`) 会记录：

- **API 请求**: 创建任务、查询状态、下载文件
- **任务创建**: 任务 ID
- **状态查询**: 任务状态、进度
- **文件下载**: 下载请求、文件路径
- **错误信息**: API 错误详情

## 配置日志级别

### 通过环境变量

在 `.env` 文件或 Docker Compose 中设置：

```env
LOG_LEVEL=DEBUG  # 或 INFO, WARNING, ERROR, CRITICAL
```

### 在 Docker Compose 中

```yaml
environment:
  - LOG_LEVEL=DEBUG
```

## 日志文件管理

loguru 自动管理日志文件：

- **文件大小限制**: 每个日志文件最大 10MB，达到后自动轮转
- **文件保留**: 自动保留最近 5 天的日志
- **文件压缩**: 旧日志自动压缩为 ZIP 格式
- **文件位置**: 
  - `logs/app.log` - 当前日志文件
  - `logs/app.log.2025-11-16_00-00-00.zip` - 压缩的旧日志文件

## 示例：查看字幕处理任务日志

```bash
# 1. 查看所有字幕相关日志
docker logs video-subtitle-api 2>&1 | grep "subtitle"

# 2. 查看特定任务的日志
docker logs video-subtitle-api 2>&1 | grep "任务 abc123"

# 3. 查看错误日志
docker logs video-subtitle-api 2>&1 | grep "ERROR"

# 4. 实时监控日志
docker logs -f video-subtitle-api 2>&1 | grep --line-buffered "subtitle"

# 5. 查看任务创建日志
docker logs video-subtitle-api 2>&1 | grep "创建字幕处理任务"

# 6. 查看处理进度
docker logs video-subtitle-api 2>&1 | grep "进度"
```

## 日志过滤示例

```bash
# 只查看字幕服务日志
docker logs video-subtitle-api 2>&1 | grep "subtitle_service"

# 只查看路由日志
docker logs video-subtitle-api 2>&1 | grep "subtitle_router"

# 查看任务创建日志
docker logs video-subtitle-api 2>&1 | grep "创建字幕处理任务"

# 查看处理进度
docker logs video-subtitle-api 2>&1 | grep "进度"

# 查看翻译相关日志
docker logs video-subtitle-api 2>&1 | grep "翻译"

# 查看优化相关日志
docker logs video-subtitle-api 2>&1 | grep "优化"
```

## 调试模式

启用 DEBUG 级别可以查看更详细的日志：

```bash
# 在 docker-compose.yml 中设置
environment:
  - LOG_LEVEL=DEBUG

# 重启服务
docker-compose restart api

# 查看详细日志
docker logs -f video-subtitle-api
```

## loguru 特性

### 自动堆栈跟踪

当发生错误时，loguru 会自动记录完整的堆栈跟踪：

```python
try:
    # 代码
except Exception as e:
    logger.error(f"错误: {e}")  # 自动包含堆栈跟踪
```

### 结构化日志

可以使用 `bind` 添加额外的上下文信息：

```python
logger = logger.bind(task_id="abc123", user_id="user1")
logger.info("处理任务")  # 会自动包含 task_id 和 user_id
```

### 性能优化

- loguru 使用异步写入，不会阻塞主线程
- 自动批量写入，提高性能
- 支持日志压缩，节省磁盘空间

## 注意事项

1. **日志文件大小**: 定期清理旧日志文件，避免占用过多磁盘空间
2. **敏感信息**: 日志中可能包含文件路径等信息，注意保护隐私
3. **性能影响**: DEBUG 级别会产生大量日志，可能影响性能，生产环境建议使用 INFO 级别
4. **Docker 日志**: Docker 容器日志默认有大小限制，可以通过 `docker-compose.yml` 配置日志驱动

## Docker 日志驱动配置

如果需要自定义 Docker 日志驱动，可以在 `docker-compose.yml` 中添加：

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```
