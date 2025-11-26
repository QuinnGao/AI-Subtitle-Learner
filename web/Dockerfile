# 构建阶段
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
ENV NEXT_TELEMETRY_DISABLED=1
# 设置生产环境变量（构建时）
ARG NEXT_PUBLIC_API_BASE_URL=/api/v1
ARG NEXT_PUBLIC_ENV=production
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_ENV=${NEXT_PUBLIC_ENV}
# 使用开发模式构建，避免静态生成问题
RUN npm run build

# 生产阶段
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 安装curl用于健康检查
RUN apk add --no-cache curl

# 创建非root用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 从构建阶段复制必要文件
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# 暴露端口
EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

# 启动应用
CMD ["node", "server.js"]

