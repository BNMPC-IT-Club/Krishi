# ক্ষেতসাথী — Smart Krishi Buddhimotta UI

This is the Next.js frontend preserved from the repository's `ui-smart-krishi-buddhimotta` main-branch UI. Its layout, styling, and **ফসল পরামর্শ** guides are retained. Server routes proxy chat, image classification, and sample-price forecasts to the Python API at `../backend/` using a server-only `BACKEND_URL`.

## Develop locally

```bash
npm ci
cp .env.example .env.local
```

Set `BACKEND_URL=http://localhost:8000` and `FRONTEND_URL=http://localhost:3000` in `.env.local`, start FastAPI from the repository root, then run:

```bash
npm run dev -- --hostname 0.0.0.0
```

Build checks:

```bash
npm run typecheck
npm run build
```

## Deploy

Use the repository-root instructions in [`../DEPLOYMENT.md`](../DEPLOYMENT.md) for Vercel, Render, Groq, Telegram webhook setup, and the limitations of free hosting. No database is required.
