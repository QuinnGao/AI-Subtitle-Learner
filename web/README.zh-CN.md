# AI Subtitle Learner 前端（Frontend）

基于 Next.js、Tailwind CSS、shadcn/ui 和 i18next 的 AI 字幕学习前端应用。

## 功能特性

- 🎬 输入 YouTube URL 获取字幕
- 📝 支持字幕文件路径输入
- 🔄 实时任务状态轮询
- 📊 进度条显示
- 🌐 国际化支持（中文/英文）
- 💾 字幕文件下载

## 技术栈

- **Next.js 14** - React 框架
- **Tailwind CSS** - 样式框架
- **shadcn/ui** - UI 组件库
- **i18next** - 国际化
- **TypeScript** - 类型安全
- **ESLint** - 代码检查
- **Prettier** - 代码格式化

## 安装

```bash
cd web
npm install
```

## 环境配置

项目支持两种运行环境：**本地开发环境** 和 **生产环境**。

### 本地开发环境（Local Development）

适用于本地开发调试，直接访问后端服务。

1. **复制环境变量示例文件**：

   ```bash
   cp .env.local.example .env.local
   ```

2. **编辑 `.env.local` 文件**：

   ```env
   # 本地开发环境配置
   # 直接访问后端服务（不通过 Nginx）
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
   NEXT_PUBLIC_ENV=development
   ```

3. **启动开发服务器**：

   ```bash
   npm run dev
   ```

**说明**：

- 本地开发时，前端运行在 `http://localhost:3000`
- 后端 API 运行在 `http://localhost:8000`
- 前端直接访问后端，不经过 Nginx 反向代理

### 生产环境（Production）

适用于 Docker 部署，通过 Nginx 反向代理访问。

1. **Docker Compose 部署**（推荐）：
   - 环境变量已在 `docker-compose.yml` 中配置
   - 默认使用相对路径 `/api/v1`
   - 通过 Nginx 反向代理统一访问

2. **手动构建生产版本**：

   ```bash
   # 复制生产环境配置
   cp .env.production.example .env.production

   # 构建生产版本
   npm run build

   # 启动生产服务器
   npm start
   ```

**说明**：

- 生产环境通过 Nginx 反向代理访问
- 前端访问地址：`http://localhost`（Nginx:80）
- API 访问路径：`/api/v1`（由 Nginx 代理到后端）

### 环境变量说明

| 变量名                    | 本地开发                        | 生产环境 | 说明       |
|---------------------------|---------------------------------|----------|------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | `/api/v1` | API 基础地址 |
| `NEXT_PUBLIC_ENV`        | `development`                  | `production` | 环境标识（可选） |

### 配置文件优先级

Next.js 环境变量加载顺序（优先级从高到低）：

1. `.env.local` - 本地开发配置（所有环境，优先级最高）
2. `.env.development` - 开发环境配置
3. `.env.production` - 生产环境配置
4. `.env` - 默认配置（所有环境）

**注意**：`.env.local` 文件不会被提交到 Git，用于本地开发配置。

## 运行

### 本地开发模式

```bash
# 1. 配置环境变量（首次运行）
cp .env.local.example .env.local
# 编辑 .env.local，设置 NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# 2. 启动开发服务器
npm run dev
```

应用将在 [http://localhost:3000](http://localhost:3000) 启动。

**前提条件**：

- 确保后端 API 服务正在运行（`http://localhost:8000`）
- 或使用 Docker Compose 启动所有服务

### 生产构建

```bash
# 构建生产版本
npm run build

# 启动生产服务器
npm start
```

### Docker 部署

使用 Docker Compose 部署（推荐）：

```bash
# 在项目根目录
docker-compose up -d web
```

生产环境配置已在 `docker-compose.yml` 中设置，无需额外配置。

## 代码质量

### Linting

```bash
npm run lint        # 检查代码问题
npm run lint:fix    # 自动修复可修复的问题
```

### 代码格式化

```bash
npm run format         # 格式化所有代码文件
npm run format:check   # 只检查格式，不修改文件
```

### 配置说明

- **ESLint**: 使用 Next.js 推荐的配置，并集成了 Prettier
- **Prettier**: 配置了 Tailwind CSS 插件，自动排序 Tailwind 类名
- **EditorConfig**: 统一编辑器配置，确保团队代码风格一致

主要配置文件：

- `.eslintrc.json` - ESLint 配置
- `.prettierrc.json` - Prettier 配置
- `.prettierignore` - Prettier 忽略文件
- `.editorconfig` - EditorConfig 配置

## 使用说明

1. 在输入框中输入 YouTube 视频 URL（例如：`https://www.youtube.com/watch?v=...`）
2. 或者直接输入字幕文件路径
3. 点击「提交」按钮创建处理任务
4. 系统会自动轮询任务状态并显示进度
5. 任务完成后可以下载处理好的字幕文件

## 项目结构

```text
web/
├── app/              # Next.js App Router
│   ├── layout.tsx    # 根布局
│   ├── page.tsx      # 主页面
│   └── globals.css   # 全局样式
├── components/       # React 组件
│   └── ui/           # shadcn/ui 组件
├── lib/              # 工具函数和配置
│   ├── api.ts        # API 客户端
│   ├── i18n.ts       # i18next 配置
│   └── utils.ts      # 工具函数
└── locales/          # 国际化文件
    ├── zh-CN.json    # 中文
    └── en-US.json    # 英文
```

## 注意事项

- 确保后端 API 服务正在运行
- YouTube URL 需要是有效的视频链接
- 字幕文件路径需要是后端可访问的路径
- 如果后端需要先下载 YouTube 视频/字幕，可能需要额外的 API 调用


