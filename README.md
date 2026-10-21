# Smart Krishi Buddhimotta 🌾
**স্মার্ট কৃষি বুদ্ধিমত্তা** — বাংলাদেশের কৃষকদের জন্য স্মার্ট কৃষি, ফসলের রোগ শনাক্তকরণ, আবহাওয়া ও বাজারদর সহায়ক প্ল্যাটফর্ম।

A Bengali-first agricultural intelligence web app built with Streamlit. Adapted and improved from the open-source [Agri-Smart-BD](https://github.com/NawrizTurjo/Agri-Smart-BD) project (original code & pretrained model weights belong to their respective authors; see LICENSE).

---

## ✨ Features that genuinely work

| Section (বাংলা) | What it does | Data source | API key needed? |
|---|---|---|---|
| 🏠 স্বাগতম / ড্যাশবোর্ড | Overview, quick stats, navigation | — | No |
| 💰 আজকের বাজারদর | Live mandi prices from **DAM (kisan bazaar)** reports; graceful error if DAM server is down; manual CSV/Excel upload supported | `market.dam.gov.bd` | No |
| 📈 ফসলের দাম পূর্বাভাস | 30-day price forecast (existing trained model, historical vs predicted chart) | Bundled **sample** dataset — clearly labelled *"নমুনা ডেটা — বাস্তব দাম নয়"* | No |
| 🍃 গাছের রোগ শনাক্তকরণ | Upload a leaf photo → PyTorch ResNet9 predicts among **38 PlantVillage classes** with confidence + Bengali advisory | Local pretrained weights (`plant_disease_weights.pth`) | No |
| 🌦️ আবহাওয়া | Current weather + multi-day forecast for all 64 districts, rain probability, farm-planning reminders | **Open-Meteo.com** (free) | **No** |
| 🤖 কৃষি সহায়ক AI | Bengali agriculture chat assistant (Llama-3.3-70B) | **Groq API** (free tier) | Yes (free key) |
| 📲 টেলিগ্রাম অ্যালার্ট | Free weather/market alert push via your own Telegram bot | **Telegram Bot API** (free) | Bot token (free) |
| ℹ️ প্রকল্প সম্পর্কে | About, data sources, limitations | — | No |

### Honest data policy
- Real market prices are shown **only** when fetched from DAM. When the DAM server is unavailable, the app says so — it never shows fake numbers as real prices.
- The bundled `bd_crop_price_data.csv` is **derived/sample data**, always labelled as such in the UI. Forecasts based on it are marked *পরীক্ষামূলক* (experimental).
- Disease model supports only its 38 PlantVillage training classes (apple, corn, potato, tomato etc.). It honestly discloses when your crop may be outside those classes.

---

## 🧠 Model weights (important for deployment)

The trained disease-detection weights (`plant_disease_weights.pth`, ~26 MB) are **not committed to this repo** to stay within GitHub size limits. On first start the app downloads them automatically from the original repo:

```
https://github.com/NawrizTurjo/Agri-Smart-BD/raw/main/plant_disease_weights.pth
```

and caches them under `.streamlit/cache/`. This works on Streamlit Cloud, Render and locally (internet needed once). If your network blocks it, download that file manually and place it next to `app.py`.


## 🚀 Run locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # optional: add keys
streamlit run app.py
```
Open http://localhost:8501 — everything works even without any keys (AI chat & Telegram show a setup hint instead).

## 🔑 Optional keys (both FREE, no credit card)

**Groq AI chat**
1. Sign up at https://console.groq.com → *API Keys* → create key.
2. Put it in `.streamlit/secrets.toml`: `GROQ_API_KEY = "gsk_..."`

**Telegram alerts**
1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.
2. Open your bot and send `/start`.
3. Add to secrets:
```toml
[telegram]
bot_token = "123456:AA..."
chat_id = ""   # leave empty — the app auto-detects it
```

⚠️ Never commit `secrets.toml` — it is git-ignored.

## ☁️ Free hosting (Streamlit Community Cloud)
1. Push this repo to GitHub (weights files included).
2. Go to https://share.streamlit.io → *New app* → pick your repo, branch, entry point `app.py`.
3. Under **Settings → Secrets**, paste the contents of `.streamlit/secrets.toml.example` with your real keys.
4. Deploy. (RAM note: choose the free tier; the model loads once and is cached.)

## 📊 Data sources & attribution
- **Weather:** [Open-Meteo](https://open-meteo.com/) (free, non-commercial, no key)
- **Market prices:** Department of Agricultural Marketing (DAM), Bangladesh — `market.dam.gov.bd`
- **Disease model:** ResNet9 weights trained on [PlantVillage](https://www.kaggle.com/datasets/emmarex/plantdisease) dataset (public research dataset); original implementation by the Agri-Smart-BD author, converted to PyTorch weights kept in this repo.
- **Sample price data:** derived from public India-agri sample datasets — **not** verified Bangladeshi prices.

## ⚠️ Limitations
- Forecasts are experimental until genuine Bangladeshi price history is uploaded (use the CSV import).
- Disease model covers 38 classes only; low-confidence results advise expert confirmation.
- DAM live fetch depends on their server availability; the app degrades gracefully.

## License
MIT (see LICENSE). Inherited components retain their original notices.
