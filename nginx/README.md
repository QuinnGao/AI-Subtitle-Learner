# Nginx Reverse Proxy

This directory contains the Nginx reverse proxy configuration used by the Docker stack.

## Routes

- `/` – Frontend app (service `web:3000`)
- `/api/v1` – Backend API (service `api:8000`)
- `/api/docs` or `/docs` – API docs (`api:8000/docs`)
- `/health` – Health check (`api:8000/health`)
- `/minio/` – MinIO console (`minio:9001`, optional)
- `/rabbitmq/` – RabbitMQ management UI (`rabbitmq:15672`, optional)

## SSE Support

SSE (Server-Sent Events) is enabled for real-time task status updates.

## Large File Uploads

Configured to support file uploads up to **500MB**.

## Usage

### Standard deployment

```bash
docker-compose up -d
```

Access:

- Frontend: `http://localhost`
- API: `http://localhost/api/v1`
- API docs: `http://localhost/docs`

### GPU deployment

```bash
docker-compose -f docker-compose.gpu.yml up -d
```

Note: the GPU compose file may not include MinIO / RabbitMQ. If these services are missing, Nginx may fail to start. Either comment out related `upstream` / `location` blocks in `nginx.conf`, or ensure these services are defined.

## Customization

Edit `nginx/nginx.conf` as needed, then restart Nginx:

```bash
docker-compose restart nginx
```

## Ports

- Nginx listens on port **80**
- Other service ports are usually commented out and accessed via the reverse proxy
- You can uncomment port mappings in Docker Compose if you need direct access

## Security Recommendations

1. **Production** – Protect MinIO and RabbitMQ management UIs with authentication.
2. **HTTPS** – Configure SSL/TLS certificates and serve over HTTPS.
3. **Firewall** – Expose only required ports (80/443) to the public.

