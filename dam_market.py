"""
DAM (Department of Agricultural Marketing, Bangladesh) live market-price fetcher.

Source: https://market.dam.gov.bd/commodity_wise_report?L=E
The site exposes a "CSV" export endpoint that actually returns an HTML table
(named .xls). We fetch it politely (session + CSRF token from the report page),
parse the table with BeautifulSoup and return a tidy pandas DataFrame.

Columns returned:
    Commodity, Division, District, Market, PriceType, Lowest_Tk_500gmlkg,
    Highest_Tk_500gmlkg, Date

Notes / honesty rules:
- Prices are per 500 g / ml / kg exactly as published by DAM.
- Only real rows fetched from the government source are returned.
- If the source is down / layout changed, we raise DamError; the UI then shows
  a clear fallback message. We NEVER fabricate prices.
"""

from __future__ import annotations

import datetime as _dt
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://market.dam.gov.bd"
REPORT_PAGE = f"{BASE_URL}/commodity_wise_report?L=E"
CSV_ENDPOINT = f"{BASE_URL}/commodity_wise_report/csv"

# commodity_group values parsed live from the page; these are stable labels.
GROUP_KEYWORDS = {
    "Foodgrains": ["Foodgrains"],
    "Pulses": ["Pulses"],
    "Dal": ["Dal"],
    "Oil Seed": ["Oil Seed"],
    "Vegetable": ["Vegetable"],
    "Fruit": ["Fruit"],
    "Spices": ["Spices"],
}

_HEADERS = {"User-Agent": "Mozilla/5.0 (Smart-Krishi-Buddhimotta; price lookup)"}


class DamError(Exception):
    """Raised when the DAM report cannot be fetched or parsed."""


def _clean_number(text: str):
    text = (text or "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_dam_prices(group_label: str, date_from: _dt.date, date_to: _dt.date,
                     timeout: int = 30) -> pd.DataFrame:
    """Fetch the DAM commodity-wise report for one commodity group.

    Returns a DataFrame with real observations only (may be empty).
    Raises DamError on network / layout failures.
    """
    s = requests.Session()
    s.headers.update(_HEADERS)

    # 1. GET the report page to obtain a fresh CSRF token + option values.
    try:
        r = s.get(REPORT_PAGE, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise DamError(f"ডিএএম ওয়েবসাইটে পৌঁছানো যায়নি: {e}") from e

    m = re.search(r'name="csrf_webspice_tkn"\s+value="([^"]+)"', r.text)
    if not m:
        raise DamError("রিপোর্ট পেজে CSRF টোকেন পাওয়া যায়নি (সাইটের গঠন বদলেছে?)।")
    csrf = m.group(1)

    # Find the exact option value for the requested group, e.g. "26|Foodgrains".
    gm = re.search(r'<option value="(\d+\|[^"]*%s[^"]*)"' % re.escape(group_label),
                   r.text, re.I)
    if not gm:
        raise DamError(f"“{group_label}” কমোডিটি গ্রুপ সাইটে খুঁজে পাওয়া যায়নি।")
    group_value = gm.group(1)

    # 2. POST to the export endpoint with filters (Wholesale + Retail prices).
    payload = {
        "csrf_webspice_tkn": csrf,
        "commodity_group": group_value,
        "Commodity_id[]": "",          # all commodities in the group
        "PriceType_id[]": ["5|Wholesale", "4|Retail"],
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_end": date_to.strftime("%Y-%m-%d"),
        "filter": "Filter",
    }
    try:
        r2 = s.post(CSV_ENDPOINT, data=payload, timeout=timeout)
    except requests.RequestException as e:
        raise DamError(f"রিপোর্ট ডাউনলোড ব্যর্থ: {e}") from e

    html = r2.text
    if "A Database Error Occurred" in html or r2.status_code >= 500:
        raise DamError("ডিএএম সার্ভারে সাময়িক সমস্যা হয়েছে (৫০০)। পরে আবার চেষ্টা করুন।")
    if r2.status_code != 200:
        raise DamError(f"ডিএএম রিপোর্ট পাওয়া যায়নি (HTTP {r2.status_code})।")

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="table") or soup.find_all("table")[-1]
    if table is None:
        raise DamError("রিপোর্টে কোনো ডেটা টেবিল পাওয়া যায়নি (সাইটের গঠন বদলেছে?)।")

    rows = []

    # Header-driven parsing (robust against column shifts).
    header_cells = [th.get_text(strip=True) for th in table.find_all("th")]
    if not header_cells:
        # first row might be a header made of td's
        first_tr = table.find("tr")
        if first_tr is None:
            raise DamError("রিপোর্ট টেবিল খালি।")
        header_cells = [td.get_text(strip=True) for td in first_tr.find_all("td")]

    def col_idx(names):
        for i, h in enumerate(header_cells):
            hl = h.lower()
            if any(n.lower() in hl for n in names):
                return i
        return None

    idx = {
        "division": col_idx(["Division"]),
        "district": col_idx(["District"]),
        "market": col_idx(["Market"]),
        "commodity": col_idx(["Commodity"]),
        "pricetype": col_idx(["Price Type", "PriceType", "Type"]),
        "low": col_idx(["Lowest"]),
        "high": col_idx(["Highest"]),
        "unit": col_idx(["Unit"]),
        "date": col_idx(["Date"]),
    }
    required = ["commodity", "low", "high", "date"]
    if any(idx[k] is None for k in required):
        raise DamError(
            f"রিপোর্টের কলাম শনাক্ত করা যায়নি। হেডার: {header_cells}")

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < max(v for v in idx.values() if v is not None) + 1:
            continue
        vals = [td.get_text(strip=True) for td in tds]
        low = _clean_number(vals[idx["low"]])
        high = _clean_number(vals[idx["high"]])
        if low is None and high is None:
            continue
        rows.append({
            "Commodity": vals[idx["commodity"]],
            "Division": vals[idx["division"]] if idx["division"] is not None else "",
            "District": vals[idx["district"]] if idx["district"] is not None else "",
            "Market": vals[idx["market"]] if idx["market"] is not None else "",
            "PriceType": vals[idx["pricetype"]] if idx["pricetype"] is not None else "",
            "Lowest_Tk": low,
            "Highest_Tk": high,
            "Unit": vals[idx["unit"]] if idx["unit"] is not None else "500g/ml/kg",
            "Date": vals[idx["date"]],
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df["Source"] = "Department of Agricultural Marketing (DAM), dam.gov.bd"
    return df
