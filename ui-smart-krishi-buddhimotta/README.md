# স্মার্ট কৃষি বুদ্ধিমত্তা — Smart Krishi Buddhimotta UI

This is the Next.js frontend preserved from the repository's `ui-smart-krishi-buddhimotta` main-branch UI. Its layout, styling, and **ফসল পরামর্শ** guides are retained. Server routes proxy chat, image classification, and sample-price forecasts to the Python API at `../backend/` using a server-only `BACKEND_URL`.

Disease assistance accepts drag-and-drop, gallery, or camera images and analyzes them automatically without a crop picker. AI explanation is opt-in. The existing ResNet9 remains limited to its 38 PlantVillage classes; treatment products are shown only for exact recorded crop/pest matches, with DAE source links and current-label/availability caveats.

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
