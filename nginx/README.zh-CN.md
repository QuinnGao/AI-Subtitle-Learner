# Nginx 反向代理配置

本目录包含用于 Docker 集群的 Nginx 反向代理配置。

## 配置说明

### 路由规则

- `/` - 前端应用 (web:3000)
- `/api/v1` - 后端 API (api:8000)
- `/api/docs` 或 `/docs` - API 文档 (api:8000/docs)
- `/health` - 健康检查 (api:8000/health)
- `/minio/` - MinIO 控制台 (minio:9001) - 可选
- `/rabbitmq/` - RabbitMQ 管理界面 (rabbitmq:15672) - 可选

### SSE 支持

配置已支持 Server-Sent Events (SSE)，用于实时任务状态更新。

### 大文件上传

配置支持最大 500MB 的文件上传。

## 使用方式

### 标准部署

```bash
docker-compose up -d
```

访问地址：

- 前端: http://localhost
- API: http://localhost/api/v1
- API 文档: http://localhost/docs

### GPU 版本部署

```bash
docker-compose -f docker-compose.gpu.yml up -d
```

**注意**: GPU 版本可能不包含 MinIO 和 RabbitMQ 服务。如果这些服务不存在，nginx 可能无法启动。如果遇到问题，可以：

1. 注释掉 `nginx.conf` 中相关的 `upstream` 和 `location` 配置
2. 或者确保这些服务在 `docker-compose.gpu.yml` 中已定义

## 自定义配置

如果需要修改配置，编辑 `nginx/nginx.conf` 文件，然后重启 nginx 服务：

```bash
docker-compose restart nginx
```

## 端口说明

- Nginx 监听端口: 80
- 其他服务的端口已注释掉，通过 nginx 反向代理访问
- 如需直接访问服务，可以在 Docker Compose 中取消注释相应的端口映射

## 安全建议

1. **生产环境**: 建议为 MinIO 和 RabbitMQ 管理界面添加认证
2. **HTTPS**: 建议配置 SSL/TLS 证书，使用 HTTPS
3. **防火墙**: 只暴露必要的端口（80/443）


