# Deploy Smart Krishi Buddhimotta

This repository is split into two deployables. The Next.js UI stays in `ui-smart-krishi-buddhimotta/`; the FastAPI service lives in `backend/`. The UI calls the Python service only through same-origin Next.js routes, so browser code never calls `localhost` or exposes service secrets.

## 1. Accounts and prerequisites

- GitHub access to this repository.
- A Vercel account for the frontend.
- A Render account (or another Python 3.11 host) for the API.
- A Groq API key only if you want chat and AI-generated disease summaries. Create it in Groq Console and store it only in Render environment variables.
- A Telegram bot token only if you want the optional bot welcome link. Create it with `@BotFather`; do not paste it into source code or chat.
- Node.js 22 for local frontend development; Python 3.11 for the API.

There is **no database setup** and no `DATABASE_URL` requirement.

## 2. Deploy the Python API to Render

1. In Render, choose **New → Blueprint** and connect this repository. Keep the repository root as the Blueprint/root directory so `render.yaml`, `backend/`, `disease_model.py`, the CSV, and the tracked model checkpoint are all available.
2. Render reads [`render.yaml`](render.yaml). It installs `backend/requirements.txt`, starts `uvicorn backend.main:app`, and checks `/health`. The included plan is `free`; you can change it to a paid plan if you need faster cold starts, more memory, or a continuously available service.
3. In the new service's **Environment** tab, add:
   - `GROQ_API_KEY` — optional; required for Groq chat and AI disease summaries. Keep it in Render only.
   - `FRONTEND_URL` — your Vercel production URL, e.g. `https://your-app.vercel.app` (no trailing slash). This is used for CORS if the API is called directly; the normal UI path is a server-side proxy.
4. Wait for the deploy to finish. Open `https://YOUR-SERVICE.onrender.com/health`. A healthy response includes `"ok": true` and `"disease_weights_present": true`.
5. Copy the Render service's base URL. You will enter it in Vercel as `BACKEND_URL`, with no trailing slash.

The disease checkpoint (`plant_disease_weights.pth`, about 26 MB) and CSV are already tracked in this repository. The model is loaded on first inference and cached in process memory; no training step occurs.

### If you use another Python host

Use Python 3.11, install `backend/requirements.txt`, and run:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Keep the repository root as the working directory. The host must allow outbound HTTPS for Groq and Open-Meteo. Its memory limit must be sufficient to import CPU PyTorch and load the model checkpoint.

## 3. Deploy the frontend to Vercel

1. In Vercel, choose **Add New → Project** and import this repository.
2. Set **Root Directory** to `ui-smart-krishi-buddhimotta`. Let Vercel detect Next.js. Use Node.js 22 if Vercel asks for a Node version.
3. In **Project → Settings → Environment Variables**, add:

   | Variable | Value | Environment |
   |---|---|---|
   | `BACKEND_URL` | `https://YOUR-SERVICE.onrender.com` | Production, Preview (and Development if desired) |
   | `FRONTEND_URL` | `https://YOUR-PRODUCTION-APP.vercel.app` | Production, Preview as appropriate |
   | `TELEGRAM_BOT_TOKEN` | BotFather token; optional | Production only |
   | `TELEGRAM_WEBHOOK_SECRET` | Random secret; optional | Production only |

   Do **not** prefix these with `NEXT_PUBLIC_`. `GROQ_API_KEY` belongs on Render, not in browser-visible frontend variables. No `DATABASE_URL` is needed.
4. Deploy (or redeploy after saving environment variables). Vercel runs `npm install` and `npm run build` from the configured root directory.
5. Visit the deployment. Test the frontend and the backend proxy at `/api/health`; the JSON should show `backend: "available"` when Render is awake.

`BACKEND_URL` is read only by Next.js server routes. Chat, disease inference, and price forecast are proxied through `/api/chat`, `/api/disease`, and `/api/forecast`. Weather continues to use the keyless Open-Meteo Next.js route; the OSM map remains client-side.

## 4. Optional: configure Telegram `/start`

The webhook is a Vercel route at `https://YOUR-PRODUCTION-APP.vercel.app/api/telegram`.

1. Open Telegram and message `@BotFather`.
2. Send `/newbot`, follow the prompts, and save the bot token privately.
3. Generate a webhook secret locally. For example, on macOS/Linux:

   ```bash
   openssl rand -hex 32
   ```

   Copy the result into Vercel as `TELEGRAM_WEBHOOK_SECRET`. Add the BotFather token as `TELEGRAM_BOT_TOKEN`, and make sure Vercel's `FRONTEND_URL` is the public HTTPS URL. Redeploy after changing environment variables.
4. From a local terminal, set the same values in temporary shell variables and register the webhook (replace the placeholder values locally; do not commit them):

   ```bash
   export TELEGRAM_BOT_TOKEN='paste-your-private-token-here'
   export TELEGRAM_WEBHOOK_SECRET='paste-the-same-random-secret-here'
   export FRONTEND_URL='https://YOUR-PRODUCTION-APP.vercel.app'

   curl --fail --silent --show-error \
     --data-urlencode "url=${FRONTEND_URL}/api/telegram" \
     --data-urlencode "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"

   unset TELEGRAM_BOT_TOKEN TELEGRAM_WEBHOOK_SECRET
   ```

   Telegram should return `"ok":true`. The token is used only by this local command and Vercel's environment; never put it in a URL committed to Git.
5. Open your bot in Telegram and send `/start`. It should reply in Bengali with a button that opens the deployed website. `/help` sends the same welcome/link.

If you rotate the webhook secret, update the Vercel variable, redeploy, then run `setWebhook` again with the new secret.

## 5. Local development

### Python API

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
export GROQ_API_KEY='your-private-key'  # optional; omit to use fallback disease advice
export FRONTEND_URL='http://localhost:3000'
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Next.js UI

In a second terminal:

```bash
cd ui-smart-krishi-buddhimotta
npm ci
cp .env.example .env.local
```

Edit `.env.local` for local use:

```dotenv
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

Then run:

```bash
npm run dev -- --hostname 0.0.0.0
```

Open `http://localhost:3000`. The local weather route uses Open-Meteo; crop guides, the map, and the interface work without Groq or Telegram credentials. If the Python service is not running, price charts fall back to the clearly labelled local demo series and AI/image features show a friendly setup/connection error.

## 6. What the data does—and does not—mean

- `bd_crop_price_data.csv` is inherited sample/derived data with records dated **2024-03-21 to 2025-05-18**. It is not a current official Bangladesh market feed. The forecast endpoint uses it as a baseline and generates a deterministic 14-day **simulation dated around today**. The generated history is not an observed current-price series, and the forecast has not been validated. Crops without CSV rows use a labelled synthetic demo baseline.
- The market table contains demo values. Do not use either screen to decide a real sale, purchase, or planting schedule.
- The existing ResNet9 predicts among 38 PlantVillage classes only. It does not cover all local crops or diseases; its score is not a calibrated probability. The response explicitly warns when a selected local crop is outside the model's crop classes. Seek confirmation from a local agriculture officer.
- Disease photos are compressed in the browser and sent to the Python API for inference. The photo is **not** sent to Groq; only top model labels/scores and the user's typed symptoms are sent for an optional text summary.
- Weather comes from Open-Meteo; forecasts may be wrong. Map tiles are from OpenStreetMap. Respect those services' current terms and attribution.

## 7. Free-tier availability: important

A free deployment is suitable for a demo, not a 24/7 guarantee. Render free web services may spin down after inactivity, have limited monthly compute and memory, and cold-start slowly. A cold start plus CPU PyTorch import/model loading can delay disease requests; a free instance may also hit memory or build limits. Vercel's free plan has its own usage and function-duration limits. **Do not promise always-awake or instant inference on free hosting.** If the app must respond reliably at all times, budget for an always-on backend plan with adequate memory and monitor its uptime. Exact provider quotas can change; check the plans shown in your accounts before launch.

## Troubleshooting

- **Chat says backend unavailable:** confirm `BACKEND_URL` in Vercel, redeploy, and check the Render `/health` endpoint. If this is the first request after inactivity, wait for Render to wake and retry.
- **Chat says Groq key missing/invalid:** set `GROQ_API_KEY` in Render (not in client code), verify it in Groq Console, and redeploy/restart the API.
- **Disease request cannot load model:** check `/health` for `disease_weights_present`; confirm `plant_disease_weights.pth` is present in the deployed Git revision and the Render instance has enough memory.
- **Forecast shows local demo fallback:** check `/api/health` and the Render service. This fallback keeps the UI usable but is not a live price feed.
- **Telegram receives no reply:** ensure `FRONTEND_URL`, token and secret match the deployed Vercel project, verify the webhook registration response, and test `/start` in a private chat with your bot.
- **Weather unavailable:** Open-Meteo is external and keyless; retry later. No Groq or Render secret is involved in the weather request.
