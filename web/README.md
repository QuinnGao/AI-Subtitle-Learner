# Video Subtitle Frontend

基于 Next.js、Tailwind CSS、shadcn/ui 和 i18next 的视频字幕处理前端应用。

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

## 安装

```bash
cd web
npm install
```

## 配置

创建 `.env.local` 文件（可选）：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

如果不设置，默认使用 `http://localhost:8000/api/v1`

## 运行

开发模式：

```bash
npm run dev
```

应用将在 [http://localhost:3000](http://localhost:3000) 启动。

生产构建：

```bash
npm run build
npm start
```

## 使用说明

1. 在输入框中输入 YouTube 视频 URL（例如：`https://www.youtube.com/watch?v=...`）
2. 或者直接输入字幕文件路径
3. 点击"提交"按钮创建处理任务
4. 系统会自动轮询任务状态并显示进度
5. 任务完成后可以下载处理好的字幕文件

## 项目结构

```
web/
├── app/              # Next.js App Router
│   ├── layout.tsx    # 根布局
│   ├── page.tsx      # 主页面
│   └── globals.css   # 全局样式
├── components/       # React 组件
│   └── ui/          # shadcn/ui 组件
├── lib/             # 工具函数和配置
│   ├── api.ts       # API 客户端
│   ├── i18n.ts      # i18next 配置
│   └── utils.ts     # 工具函数
└── locales/         # 国际化文件
    ├── zh-CN.json   # 中文
    └── en-US.json   # 英文
```

## 注意事项

- 确保后端 API 服务正在运行
- YouTube URL 需要是有效的视频链接
- 字幕文件路径需要是后端可访问的路径
- 如果后端需要先下载 YouTube 视频/字幕，可能需要额外的 API 调用

