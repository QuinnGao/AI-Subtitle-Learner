# AI Subtitle Learner Frontend

AI Subtitle Learner frontend built with Next.js, Tailwind CSS, shadcn/ui and i18next.

## Features

- 🎬 Input YouTube URL to get subtitles
- 📝 Support providing subtitle file path
- ✅ Real-time URL validation with visual error feedback
- 🔔 Modern toast notifications (Sonner)
- 🔄 Real-time task status updates via SSE (Server-Sent Events)
- 📊 Progress bar display
- 🌐 i18n support (Chinese / English)
- 💾 Download processed subtitle files
- 🎨 Beautiful, responsive UI with smooth animations

## Tech Stack

- **Next.js 16** – React framework with App Router
- **React 19** – Latest React with improved performance
- **Tailwind CSS** – Utility-first CSS framework
- **shadcn/ui** – High-quality UI component library
- **Sonner** – Modern toast notification system
- **i18next** – Internationalization
- **TypeScript 5.6+** – Type safety
- **React Player** – Video player component
- **ESLint** / **Prettier** – Linting & formatting
- **pnpm** – Fast, disk space efficient package manager

## Installation

```bash
cd web
pnpm install
```

## Environment & Running

### Local development

- Backend API: `http://localhost:8000`
- Frontend dev server: `http://localhost:3000`
- Example `.env.local`:

  ```env
  NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
  NEXT_PUBLIC_ENV=development
  ```

- Start dev server:

  ```bash
  pnpm run dev
  ```

### Production / Docker

- Usually served behind Nginx at `http://localhost`
- API base path: `/api/v1` (proxied by Nginx)
- Build & start:

  ```bash
  pnpm run build
  pnpm start
  ```

- Or via Docker Compose from project root:

  ```bash
  docker-compose up -d web
  ```

## Code Quality

- Lint: `pnpm run lint` / `pnpm run lint:fix`
- Format: `pnpm run format` / `pnpm run format:check`

## Usage

1. Enter a YouTube video URL (e.g. `https://www.youtube.com/watch?v=...`) or a subtitle file path.
2. The system validates the URL in real-time:
   - Invalid URLs show red borders and shake animation
   - Error state persists until a valid URL is entered
3. Click **Submit** to create a processing task.
4. The frontend receives real-time task status updates via SSE and shows progress.
5. After completion, download the processed subtitle file.
6. Use the interactive dictionary by right-clicking on words in subtitles.

## Project Structure

```text
web/
├── app/              # Next.js App Router
├── components/       # React components (incl. shadcn/ui)
├── lib/              # API client, i18n config, utilities
└── locales/          # i18n resources (zh-CN / en-US)
```

