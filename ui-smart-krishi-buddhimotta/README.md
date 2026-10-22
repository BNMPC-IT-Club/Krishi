# স্মার্ট কৃষি বুদ্ধিমত্তা — Smart Krishi Buddhimotta UI

This is the Next.js frontend preserved from the repository's `ui-smart-krishi-buddhimotta` main-branch UI. Its layout, styling, and **ফসল পরামর্শ** guides are retained. Server routes proxy chat, image classification, and sample-price forecasts to the Python API at `../backend/` using a server-only `BACKEND_URL`.

Disease assistance accepts drag-and-drop, gallery, or camera images and analyzes them automatically without a crop picker. When `GROQ_API_KEY` is configured, the backend sends the compressed image to Groq Qwen Vision for a short visual crop/disease estimate; the 38-class ResNet9 is a supporting signal or local fallback, not a universal Bangladesh crop detector. The UI discloses this image transfer before upload. Without Groq, the limited local classifier is a fallback and cannot unlock pesticide advice on its own. Longer AI explanation is opt-in and text-only. Product names/rates/application details come only from exact DAE PPW crop–disease records; unknown or uncertain pairs get safe nonchemical steps and no invented prescription.

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
