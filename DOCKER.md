# Docker 部署指南

本文档说明如何使用 Docker Compose 部署视频字幕处理系统的前端和后端服务。

## 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+

## 快速开始

### 1. 标准部署（CPU版本）

```bash
# 启动所有服务（API + Web前端）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. GPU 版本部署

如果您的系统支持 NVIDIA GPU，可以使用 GPU 版本：

```bash
# 启动 GPU 版本
docker-compose -f docker-compose.gpu.yml up -d

# 查看服务状态
docker-compose -f docker-compose.gpu.yml ps

# 停止服务
docker-compose -f docker-compose.gpu.yml down
```

## 服务访问

启动成功后，可以通过以下地址访问：

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 环境变量配置

### 前端配置

在 `.env` 文件中设置前端API地址（可选）：

```env
# 前端API地址（浏览器访问时使用）
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

**注意**：
- 如果前端和后端在同一主机，使用 `http://localhost:8000/api/v1`
- 如果使用反向代理（如nginx），可以设置为相对路径 `/api/v1`
- 如果前端和后端在不同主机，使用实际IP或域名

### 后端配置

在 `.env` 文件中配置后端服务：

```env
# LLM 配置（可选）
OPENAI_API_BASE=your_api_base
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=your_model

# 翻译服务配置（可选）
DEEPLX_ENDPOINT=your_deeplx_endpoint

# 日志配置
DEBUG=False
LOG_LEVEL=INFO
```

## 服务说明

### API 服务

- **容器名**: `video-subtitle-api` (标准版) 或 `video-subtitle-api-gpu` (GPU版)
- **端口**: 8000
- **健康检查**: http://localhost:8000/health

### Web 前端服务

- **容器名**: `video-subtitle-web`
- **端口**: 3000
- **健康检查**: http://localhost:3000

## 数据持久化

以下目录会被挂载到容器中，数据会持久化保存：

- `./workspace` - 工作目录（处理中的文件）
- `./models` - AI 模型目录
- `./logs` - 日志目录
- `./input` - 输入文件目录（只读）
- `./output` - 输出文件目录

## 构建和更新

### 重新构建镜像

```bash
# 标准版
docker-compose build

# GPU版
docker-compose -f docker-compose.gpu.yml build
```

### 仅构建前端

```bash
docker-compose build web
```

### 仅构建后端

```bash
docker-compose build api
```

## 故障排查

### 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs web
docker-compose logs api

# 实时跟踪日志
docker-compose logs -f web
```

### 检查服务健康状态

```bash
# 检查API健康状态
curl http://localhost:8000/health

# 检查前端健康状态
curl http://localhost:3000
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart web
docker-compose restart api
```

### 进入容器调试

```bash
# 进入前端容器
docker-compose exec web sh

# 进入后端容器
docker-compose exec api bash
```

## 网络配置

所有服务都在 `video-subtitle-network` 网络中，服务之间可以通过服务名互相访问：

- 前端访问后端: `http://api:8000`
- 后端访问前端: `http://web:3000`

**注意**: 浏览器无法直接访问容器内的服务名，需要使用 `localhost` 或实际IP地址。

## 生产环境建议

1. **使用反向代理**: 建议使用 Nginx 或 Traefik 作为反向代理
2. **HTTPS**: 配置 SSL 证书启用 HTTPS
3. **环境变量**: 使用 `.env` 文件管理敏感配置，不要提交到版本控制
4. **资源限制**: 根据服务器配置设置适当的资源限制
5. **日志管理**: 配置日志轮转和集中日志管理
6. **监控**: 配置健康检查和监控告警

## 示例：使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

然后在 `.env` 中设置：

```env
NEXT_PUBLIC_API_BASE_URL=/api/v1
```

