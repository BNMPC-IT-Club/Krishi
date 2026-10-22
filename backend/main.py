"""FastAPI backend for the Next.js Smart Krishi frontend.

The UI stays in ``ui-smart-krishi-buddhimotta``. This API provides Groq chat,
existing ResNet9 image inference, prototype-price calculations from the bundled
CSV, and an optional Open-Meteo proxy. It does not retrain any model.
"""
from __future__ import annotations

import base64
import csv
import datetime as dt
import io
import math
import os
import re
import sys
import threading
import zlib
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, UnidentifiedImageError

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.ai_service import complete, disease_summary
from backend.data_mappings import (
    CROP_BN_TO_SAMPLE_EN,
    DEMO_BASE_PRICES,
    DISTRICT_ALIASES,
    DISTRICT_BN_TO_EN,
)
from backend.disease_labels import DISEASE_TRANSLATION


app = FastAPI(
    title="ক্ষেতসাথী কৃষি API",
    description="Next.js UI-র জন্য ঐচ্ছিক Python API; প্রোটোটাইপ ডেটা স্পষ্টভাবে চিহ্নিত।",
    version="1.0.0",
)

_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
_allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if _frontend_url:
    _allowed_origins.append(_frontend_url)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://[a-zA-Z0-9-]+\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

CSV_PATH = _REPO_ROOT / "bd_crop_price_data.csv"
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000
BANGLA_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
MODEL_CROP_NAMES = {"আপেল", "ব্লুবেরি", "চেরি", "ভুট্টা", "আঙুর", "কমলা", "পীচ", "ক্যাপসিকাম", "আলু", "রাস্পবেরি", "সয়াবিন", "স্কোয়াশ", "স্ট্রবেরি", "টমেটো"}


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1800)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=10)
    context: str | None = Field(default=None, max_length=1000)


class DiseaseRequest(BaseModel):
    image_data_url: str = Field(min_length=50, max_length=3_000_000)
    crop: str = Field(default="", max_length=100)
    symptom: str = Field(default="", max_length=500)


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _canonical_district(value: str) -> str:
    raw = str(value or "").strip()
    if raw in DISTRICT_BN_TO_EN:
        raw = DISTRICT_BN_TO_EN[raw]
    if raw == "নেত্রকোণা":
        raw = "Netrokona"
    key = raw.casefold().strip()
    if key in DISTRICT_ALIASES:
        key = DISTRICT_ALIASES[key]
    # Preserve a stable, title-cased value for comparisons with the dataset.
    return key.title() if key else "Dhaka"


def _canonical_crop(value: str) -> str:
    raw = str(value or "").strip()
    if raw in CROP_BN_TO_SAMPLE_EN:
        raw = CROP_BN_TO_SAMPLE_EN[raw]
    key = _normalize_key(raw)
    aliases = {
        "chilli": "chilli", "chili": "chilli", "rice": "rice",
        "gram": "gram", "oilseeds": "oilseeds", "pulses": "pulses",
    }
    return aliases.get(key, key)


@lru_cache(maxsize=1)
def _read_price_rows() -> list[dict[str, Any]]:
    """Load the tracked prototype CSV once. Never imply it is current/live data."""
    if not CSV_PATH.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                crop = _canonical_crop(row.get("Crop_Name", ""))
                # Inherited sample data includes a non-food commodity; do not expose it.
                if crop == "opium":
                    continue
                try:
                    price = float(row.get("Price_Tk_kg", ""))
                    date = dt.date.fromisoformat(str(row.get("Price_Date", ""))[:10])
                except (TypeError, ValueError):
                    continue
                if not math.isfinite(price) or price <= 0:
                    continue
                rows.append({
                    "district": _canonical_district(row.get("District_Name", "")),
                    "crop": crop,
                    "date": date,
                    "price": price,
                })
    except OSError:
        return []
    return rows


def _bn_date(value: dt.date) -> str:
    return f"{value.day:02d}/{value.month:02d}".translate(BANGLA_DIGITS)


def _bn_full_date(value: dt.date) -> str:
    return f"{value.day:02d}/{value.month:02d}/{value.year}".translate(BANGLA_DIGITS)


def _forecast_from_sample(district: str, crop_bn: str, crop_key: str) -> dict[str, Any]:
    rows = _read_price_rows()
    district_key = _canonical_district(district)
    crop_rows = [row for row in rows if row["crop"] == crop_key]
    district_rows = [row for row in crop_rows if row["district"] == district_key]

    if district_rows:
        source_rows = district_rows
        source_label = "সংযুক্ত নমুনা CSV · নির্বাচিত জেলার রেকর্ড"
        scope = "district sample"
    elif crop_rows:
        source_rows = crop_rows
        source_label = "সংযুক্ত নমুনা CSV · অন্য জেলার নমুনা থেকে গড়"
        scope = "cross-district sample"
    else:
        source_rows = []
        source_label = "সার্ভার-সিমুলেটেড ডেমো · এই ফসলের CSV রেকর্ড নেই"
        scope = "synthetic demo"

    today = dt.datetime.now(ZoneInfo("Asia/Dhaka")).date()
    seed = zlib.crc32(f"{district_key}|{crop_key}".encode("utf-8"))
    if source_rows:
        source_rows = sorted(source_rows, key=lambda row: row["date"])
        latest_date = source_rows[-1]["date"]
        sample_as_of = latest_date.isoformat()
        if scope == "district sample":
            source_label = f"নমুনা CSV · নির্বাচিত জেলার রেকর্ড, সর্বশেষ {_bn_full_date(latest_date)}"
        else:
            source_label = f"নমুনা CSV · অন্য জেলার সম্মিলিত রেকর্ড, সর্বশেষ {_bn_full_date(latest_date)}"
        base = float(source_rows[-1]["price"])
        recent = source_rows[-14:]
        if len(recent) > 1:
            x_mean = (len(recent) - 1) / 2
            y_mean = sum(item["price"] for item in recent) / len(recent)
            denominator = sum((i - x_mean) ** 2 for i in range(len(recent)))
            slope = (
                sum((i - x_mean) * (item["price"] - y_mean) for i, item in enumerate(recent))
                / denominator if denominator else 0.0
            )
            trend = max(-0.003, min(0.003, slope / max(base, 1.0)))
        else:
            trend = 0.0
    else:
        latest_date = None
        sample_as_of = ""
        base = float(DEMO_BASE_PRICES.get(crop_bn, 50.0))
        trend = (((seed >> 8) % 7) - 3) * 0.00045

    phase = (seed % 29) / 29 * (2 * math.pi)

    def cycle(position: int) -> float:
        return math.sin(position / 5.8 + phase) * 0.012

    history: list[dict[str, Any]] = []
    for index in range(14):
        relative = index - 13
        value = max(1.0, base * (1 + trend * relative + cycle(relative)))
        history_date = today - dt.timedelta(days=13 - index)
        history.append({"day": _bn_date(history_date), "price": round(value, 2)})

    last_price = history[-1]["price"]
    future: list[dict[str, Any]] = []
    for day in range(1, 15):
        movement = trend * day + cycle(day) - cycle(0)
        value = max(1.0, last_price * (1 + movement))
        future_date = today + dt.timedelta(days=day)
        future.append({"day": _bn_date(future_date), "price": round(value, 2)})

    average = sum(item["price"] for item in future) / len(future)
    return {
        "district": district,
        "crop": crop_bn,
        "history": history,
        "forecast": future,
        "latest_price": last_price,
        "average_price": round(average, 2),
        "source": source_label,
        "scope": scope,
        "sample_data_as_of": sample_as_of,
        "data_kind": "prototype_non_live",
        "note": (
            "সব দাম নমুনা বা সিমুলেটেড; CSV-র তারিখ ২০২৫-০৫-১৮-এ শেষ। "
            "চার্টের তারিখ ও ভবিষ্যৎ রেখা প্রদর্শনী সিমুলেশন, বাস্তব বাজারদর বা যাচাইকৃত পূর্বাভাস নয়।"
        ),
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "smart-krishi-api",
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "disease_weights_present": (_REPO_ROOT / "plant_disease_weights.pth").is_file(),
    }


@app.get("/api/forecast")
def price_forecast(
    district: str = Query(default="ঢাকা", max_length=80),
    crop: str = Query(default="ধান", max_length=80),
) -> dict[str, Any]:
    return _forecast_from_sample(district, crop, _canonical_crop(crop))


@app.get("/api/weather")
def weather(
    lat: float = Query(...),
    lng: float = Query(...),
) -> dict[str, Any]:
    if not (math.isfinite(lat) and math.isfinite(lng)):
        raise HTTPException(status_code=400, detail="অবস্থানের স্থানাঙ্ক সঠিক নয়।")
    if not (20.3 <= lat <= 26.9 and 88.0 <= lng <= 93.7):
        raise HTTPException(status_code=400, detail="বাংলাদেশের একটি বৈধ অবস্থান নির্বাচন করুন।")
    query = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,sunrise,sunset",
        "timezone": "Asia/Dhaka",
        "forecast_days": 7,
    }
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=query,
            timeout=(4, 10),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or "current" not in payload or "daily" not in payload:
            raise ValueError("Open-Meteo response is incomplete")
    except (requests.RequestException, ValueError):
        raise HTTPException(status_code=502, detail="Open-Meteo থেকে আবহাওয়ার তথ্য পাওয়া যায়নি।") from None
    return {
        "weather": payload,
        "source": "Open-Meteo",
        "fetchedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    if not os.getenv("GROQ_API_KEY", "").strip():
        raise HTTPException(
            status_code=503,
            detail="AI সহকারী চালু করতে backend-এ GROQ_API_KEY যোগ করুন। অন্য সব ফিচার ব্যবহার করা যাবে।",
        )
    messages = [{"role": item.role, "content": item.content} for item in request.messages]
    if request.context:
        for index, message in enumerate(messages):
            if message["role"] == "user":
                messages[index] = {
                    "role": "user",
                    "content": f"প্রাসঙ্গিক অ্যাপ তথ্য: {request.context}\n\nপ্রশ্ন/বার্তা: {message['content']}",
                }
                break
    answer, model, error = complete(messages, max_tokens=750)
    if not answer:
        if error == "invalid_key":
            raise HTTPException(status_code=503, detail="Groq API key যাচাই করা যায়নি।")
        if error == "rate_limit":
            raise HTTPException(status_code=503, detail="Groq-এর অনুরোধসীমা সাময়িকভাবে পূর্ণ। পরে আবার চেষ্টা করুন।")
        raise HTTPException(status_code=502, detail="AI সেবাটি এখন সাড়া দিচ্ছে না। পরে আবার চেষ্টা করুন।")
    return {"answer": answer, "model": model}


_DISEASE_RUNTIME: tuple[Any, Any] | None = None
_DISEASE_LOAD_LOCK = threading.Lock()


def _load_disease_model():
    """Load the already-trained checkpoint once per process; never retrain or double-load."""
    global _DISEASE_RUNTIME
    if _DISEASE_RUNTIME is not None:
        return _DISEASE_RUNTIME
    with _DISEASE_LOAD_LOCK:
        if _DISEASE_RUNTIME is not None:
            return _DISEASE_RUNTIME
        import torch  # imported lazily so health/chat/forecast can start without inference loaded
        from disease_model import load_resnet9

        weights_path = _REPO_ROOT / "plant_disease_weights.pth"
        if not weights_path.is_file():
            raise FileNotFoundError("plant_disease_weights.pth is missing from the repository checkout")
        model = load_resnet9(str(weights_path))
        model.eval()
        _DISEASE_RUNTIME = (model, torch)
        return _DISEASE_RUNTIME


def _parse_image_data_url(image_data_url: str) -> bytes:
    match = re.fullmatch(r"data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=\r\n]+)", image_data_url.strip())
    if not match:
        raise HTTPException(status_code=400, detail="JPG, PNG বা WebP ছবি যোগ করুন।")
    encoded = match.group(2)
    if len(encoded) > 2_900_000:
        raise HTTPException(status_code=413, detail="ছবির আকার কমিয়ে আবার চেষ্টা করুন।")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        raise HTTPException(status_code=400, detail="ছবির তথ্য পড়া যায়নি।") from None
    if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="ছবিটি ২ এমবি-র বেশি। ছোট ছবি দিয়ে আবার চেষ্টা করুন।")
    return image_bytes


def _display_class(class_label: str) -> tuple[str, str]:
    display = DISEASE_TRANSLATION.get(class_label, class_label.replace("___", " — ").replace("_", " "))
    crop_key = class_label.split("___", 1)[0]
    crop_names = {
        "Apple": "আপেল", "Blueberry": "ব্লুবেরি", "Cherry_(including_sour)": "চেরি",
        "Corn_(maize)": "ভুট্টা", "Grape": "আঙুর", "Orange": "কমলা", "Peach": "পীচ",
        "Pepper,_bell": "ক্যাপসিকাম", "Potato": "আলু", "Raspberry": "রাস্পবেরি",
        "Soybean": "সয়াবিন", "Squash": "স্কোয়াশ", "Strawberry": "স্ট্রবেরি", "Tomato": "টমেটো",
    }
    return crop_names.get(crop_key, crop_key.replace("_", " ")), display


@app.post("/api/disease")
def disease(request: DiseaseRequest) -> dict[str, Any]:
    image_bytes = _parse_image_data_url(request.image_data_url)
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="ছবির রেজোলিউশন কমিয়ে আবার চেষ্টা করুন।")
            source.verify()
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image = image.resize((256, 256), Image.Resampling.LANCZOS)
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="ছবিটি পড়া যায়নি। অন্য JPG, PNG বা WebP ছবি দিন।") from None

    try:
        import numpy as np
        from disease_model import CLASS_LABELS, predict_torch
        model, torch = _load_disease_model()
        pixels = np.asarray(image, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(pixels).permute(2, 0, 1).unsqueeze(0)
        probabilities = np.asarray(predict_torch(model, tensor), dtype=np.float64)
        if probabilities.ndim != 1 or len(probabilities) != len(CLASS_LABELS):
            raise ValueError("model class count does not match the checkpoint")
        probabilities = np.nan_to_num(probabilities, nan=0.0, posinf=0.0, neginf=0.0)
        probabilities = np.clip(probabilities, 0.0, 1.0)
        if probabilities.sum() <= 0:
            raise ValueError("model returned no valid scores")
        probabilities = probabilities / probabilities.sum()
        top_indices = np.argsort(probabilities)[::-1][:3]
        top_predictions = []
        for index in top_indices:
            crop_label, disease_label = _display_class(CLASS_LABELS[int(index)])
            top_predictions.append({
                "class_label": CLASS_LABELS[int(index)],
                "crop_label": crop_label,
                "label": disease_label,
                "score_percent": round(float(probabilities[int(index)] * 100), 1),
            })
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="বিদ্যমান রোগ মডেলটি লোড বা চালানো যায়নি। পরে আবার চেষ্টা করুন।",
        ) from None

    prediction = top_predictions[0]
    selected_crop = request.crop.strip()
    known_local = {"ধান", "বোরো ধান", "আমন ধান", "পাট", "আখ", "সরিষা", "মসুর ডাল", "কাঁচামরিচ", "শসা", "বাঁধাকপি", "ফুলকপি", "বেগুন", "গম", "আলু", "টমেটো", "ভুট্টা", "কলা", "পেঁপে", "পেঁয়াজ", "রসুন", "আদা"}
    crop_out_of_scope = bool(selected_crop and selected_crop in known_local and selected_crop not in MODEL_CROP_NAMES)
    if crop_out_of_scope:
        scope_warning = (
            f"আপনি {selected_crop} নির্বাচন করেছেন, কিন্তু বিদ্যমান ছবির মডেলে এই ফসলের শ্রেণি নেই। "
            "ফলাফলটি ভুল হতে পারে; এটি ওই ফসলের রোগ শনাক্ত করার প্রমাণ নয়।"
        )
    else:
        scope_warning = "মডেল স্কোর ক্যালিব্রেটেড সম্ভাবনা নয়; এটি নিশ্চিত রোগনির্ণয়ও নয়।"

    answer, model_name, ai_error = disease_summary(
        prediction["crop_label"], prediction["label"], prediction["score_percent"],
        top_predictions, request.symptom,
    )
    if not answer:
        ai_note = (
            "ঐচ্ছিক Groq AI সারাংশ পাওয়া যায়নি। ছবিটি শুধু বিদ্যমান মডেলে বিশ্লেষিত হয়েছে; "
            "শ্রেণি-স্কোর নিশ্চিত রোগ বা চিকিৎসার প্রমাণ নয়। পাতার দুই পাশ পরীক্ষা করুন, "
            "আক্রান্ত গাছ আলাদা করে পর্যবেক্ষণ করুন এবং উপজেলা কৃষি অফিসারের পরামর্শ নিন।"
        )
    else:
        ai_note = answer

    return {
        "prediction": prediction,
        "top_predictions": top_predictions,
        "crop_out_of_scope": crop_out_of_scope,
        "scope_warning": scope_warning,
        "summary": ai_note,
        "summary_model": model_name,
        "summary_available": answer is not None,
        "summary_error_code": ai_error,
        "image_sent_to_groq": False,
        "data_kind": "existing_pretrained_model",
    }
