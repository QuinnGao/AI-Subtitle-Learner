FROM nginx:alpine

# 安装 wget 用于健康检查
RUN apk add --no-cache wget

# 复制配置文件
COPY nginx.conf /etc/nginx/nginx.conf

