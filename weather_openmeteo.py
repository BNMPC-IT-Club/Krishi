"""Open-Meteo weather integration (no API key required).

Provides current conditions + multi-day forecast for Bangladeshi districts
using real coordinates, plus simple farm-planning advice derived strictly
from the returned forecast variables.
"""
import requests

# Real coordinates (lat, lon) for the 64 districts of Bangladesh
DISTRICT_COORDS = {
    'Dhaka': (23.8103, 90.4125), 'Gazipur': (23.9999, 90.4205), 'Narayanganj': (23.6103, 90.4999),
    'Tangail': (24.2513, 89.9167), 'Kishoreganj': (24.4433, 90.7781), 'Manikganj': (23.8619, 90.0000),
    'Munshiganj': (23.5454, 90.5283), 'Narsingdi': (23.9231, 90.8572), 'Rajbari': (23.7608, 89.6430),
    'Madaripur': (23.1641, 90.1842), 'Gopalganj': (23.0055, 89.8250), 'Shariatpur': (23.2415, 90.4300),
    'Faridpur': (23.6070, 89.8430), 'Chattogram': (22.3569, 91.7832), "Cumilla": (23.4607, 91.1809),
    'Lakshmipur': (22.9430, 90.8380), 'Noakhali': (22.8696, 91.0982), 'Feni': (23.0156, 91.3981),
    'Brahmanbaria': (23.9950, 90.9300), 'Chandpur': (23.2335, 90.6700), 'Habiganj': (24.3750, 91.4147),
    'Maulvibazar': (24.0120, 91.7680), 'Sunamganj': (25.0658, 91.3950), 'Sylhet': (24.8936, 91.8687),
    'Rajshahi': (24.3745, 88.6042), 'Bogura': (24.8500, 89.0000), 'Pabna': (24.0050, 89.2500),
    'Sirajganj': (24.1500, 89.7000), 'Natore': (24.4200, 89.0000), 'Chapainawabganj': (24.6000, 88.2700),
    'Joypurhat': (25.0958, 89.0200), 'Naogaon': (24.8000, 88.9300), 'Khulna': (22.8456, 89.5403),
    'Jashore': (23.1667, 89.2167), 'Satkhira': (22.7200, 89.0700), 'Magura': (23.4850, 89.6200),
    'Narail': (23.1300, 89.5000), 'Jhenaidah': (23.5400, 89.1800), 'Chuadanga': (23.6400, 88.8600),
    'Meherpur': (23.7600, 88.9900), 'Kushtia': (23.9000, 89.1200), 'Barishal': (22.7020, 90.3680),
    'Patuakhali': (22.3570, 90.3280), 'Barguna': (22.1570, 90.1270), 'Bhola': (22.6850, 90.6500),
    'Pirojpur': (22.5840, 89.9700), 'Jhalokati': (22.6400, 90.2000), 'Bandarban': (22.1950, 92.2250),
    'Rangamati': (23.1330, 92.6250), 'Khagrachhari': (23.1200, 91.9800), 'Coxs Bazar': (21.4272, 92.0058),
    'Rangpur': (25.7439, 89.2752), 'Dinajpur': (25.6200, 88.6500), 'Kurigram': (25.8070, 89.6470),
    'Gaibandha': (25.3350, 89.5350), 'Nilphamari': (25.9570, 89.0500),
    'Panchagarh': (26.3350, 88.5540), 'Thakurgaon': (26.0330, 88.4670), 'Lalmonirhat': (25.8970, 89.2800),
    'Mymensingh': (24.7500, 90.4000), 'Jamalpur': (24.9300, 89.9300), 'Netrokona': (24.8700, 91.0900),
    'Sherpur': (25.0200, 90.0100),
}
# Aliases for alternate English spellings used in bundled datasets/UI
DISTRICT_COORDS.update({
    'Bogra': DISTRICT_COORDS['Bogura'],
    'Moulvibazar': DISTRICT_COORDS['Maulvibazar'],
    'Barisal': DISTRICT_COORDS['Barishal'],
    'Bhola': (22.6859, 90.6482), 'Bagerhat': (22.6517, 89.7940),
})


WEATHER_CODES = {
    0: ("পরিষ্কার আকাশ", "Clear"), 1: ("আংশিক মেঘলা", "Partly cloudy"), 2: ("মেঘলা", "Cloudy"),
    3: ("Fully cloudy", "Cloudy"), 45: ("কুয়াশা", "Fog"), 48: ("হিম-কুয়াশা", "Fog"),
    51: ("হালকা গুঁড়ি বৃষ্টি", "Light rain"), 53: ("গুঁড়ি বৃষ্টি", "Rain"), 55: ("তীব্র গুঁড়ি বৃষ্টি", "Rain"),
    61: ("হালকা বৃষ্টি", "Rain"), 63: ("মাঝারি বৃষ্টি", "Rain"), 65: ("ভারী বৃষ্টি", "Heavy rain"),
    80: ("হঠাৎ বৃষ্টি", "Showers"), 81: ("মাঝারি হঠাৎ বৃষ্টি", "Showers"), 82: ("প্রচণ্ড হঠাৎ বৃষ্টি", "Heavy showers"),
    95: ("মুষলধারা বৃষ্টি ও বজ্রপাত", "Storm"), 96: ("শিলাবৃষ্টিসহ বজ্রপাত", "Storm"), 99: ("ভারী শিলাবৃষ্টি", "Storm"),
}


def weather_code_info(code):
    return WEATHER_CODES.get(int(code), ("—", "Info"))


def _fetch(params):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def get_current_weather(lat, lon):
    """Current conditions dict or None on failure."""
    try:
        data = _fetch({
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                       "precipitation,weather_code,wind_speed_10m",
            "timezone": "Asia/Dhaka",
        })
        cur = data.get("current", {})
        return {
            "temp": cur.get("temperature_2m"),
            "feels": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "rain_mm": cur.get("precipitation"),
            "code": cur.get("weather_code", 0),
            "wind": cur.get("wind_speed_10m"),
            "time": cur.get("time"),
        }
    except Exception:
        return None


def get_forecast(lat, lon, days=7):
    """Daily forecast list of dicts or None on failure."""
    try:
        data = _fetch({
            "latitude": lat, "longitude": lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
            "forecast_days": days,
            "timezone": "Asia/Dhaka",
        })
        d = data.get("daily", {})
        out = []
        for i in range(len(d.get("time", []))):
            out.append({
                "date": d["time"][i],
                "code": d["weather_code"][i],
                "tmax": d["temperature_2m_max"][i],
                "tmin": d["temperature_2m_min"][i],
                "rain_mm": d["precipitation_sum"][i],
                "rain_prob": d["precipitation_probability_max"][i],
                "wind": d["wind_speed_10m_max"][i],
            })
        return out
    except Exception:
        return None


def farm_advice(current, forecast):
    """Cautious Bangla reminders derived ONLY from actual forecast values."""
    tips = []
    if forecast:
        tomorrow = forecast[1] if len(forecast) > 1 else None
        today = forecast[0]
        for day, label in ((tomorrow, "আগামীকাল"), (today, "আজ")):
            if not day:
                continue
            prob = day.get("rain_prob") or 0
            mm = day.get("rain_mm") or 0
            if prob >= 60 or mm >= 10:
                tips.append(f"⚠️ {label} প্রবল বৃষ্টির সম্ভাবনা ({prob}% / {mm} মিমি) — কর্তন, রোপণ বা সার/ওষুধ স্প্রে পরিস্থিতি বুঝে পরিকল্পনা করুন।")
            elif prob >= 35:
                tips.append(f"🌦️ {label} বৃষ্টির সম্ভাবনা {prob}% — মাঠে কাজের আগে আকাশ ও আপডেট দেখে নিন।")
        hot = [d for d in forecast[:3] if (d.get("tmax") or 0) >= 38]
        if hot:
            tips.append("🥵 তাপমাত্রা বেশি থাকতে পারে — ফসলে সকাল বা সন্ধ্যায় সেচ দিন এবং কৃষকদের দুপুরে মাঠে কাজ এড়িয়ে চলতে পরামর্শ দিন।")
        windy = [d for d in forecast[:3] if (d.get("wind") or 0) >= 40]
        if windy:
            tips.append("💨 বাতাস তীব্র থাকতে পারে — স্প্রে করা ওষুধ/সারের সময় সাবধান থাকুন।")
    if not tips:
        tips.append("✅ পূর্বাভানুযায়ী বিশেষ ঝুঁকির ইঙ্গিত নেই; স্বাভাবিক মাঠ তদারকি চালিয়ে যান।")
    return tips
