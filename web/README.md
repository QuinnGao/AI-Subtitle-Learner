# AI Subtitle Learner Frontend

AI Subtitle Learner frontend built with Next.js, Tailwind CSS, shadcn/ui and i18next.

## Features

- 🎬 Input YouTube URL to get subtitles
- 📝 Support providing subtitle file path
- 🔄 Polling for task status in real time
- 📊 Progress bar display
- 🌐 i18n support (Chinese / English)
- 💾 Download processed subtitle files

## Tech Stack

- **Next.js 14** – React framework
- **Tailwind CSS** – Styling
- **shadcn/ui** – UI components
- **i18next** – Internationalization
- **TypeScript** – Type safety
- **ESLint** / **Prettier** – Linting & formatting

## Installation

```bash
cd web
npm install
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
  npm run dev
  ```

### Production / Docker

- Usually served behind Nginx at `http://localhost`
- API base path: `/api/v1` (proxied by Nginx)
- Build & start:

  ```bash
  npm run build
  npm start
  ```

- Or via Docker Compose from project root:

  ```bash
  docker-compose up -d web
  ```

## Code Quality

- Lint: `npm run lint` / `npm run lint:fix`
- Format: `npm run format` / `npm run format:check`

## Usage

1. Enter a YouTube video URL (e.g. `https://www.youtube.com/watch?v=...`) or a subtitle file path.
2. Click **Submit** to create a processing task.
3. The frontend polls task status and shows progress.
4. After completion, download the processed subtitle file.

## Project Structure

```text
web/
├── app/              # Next.js App Router
├── components/       # React components (incl. shadcn/ui)
├── lib/              # API client, i18n config, utilities
└── locales/          # i18n resources (zh-CN / en-US)
```

