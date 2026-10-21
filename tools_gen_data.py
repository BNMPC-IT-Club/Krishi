"""One-off generator: regenerate the bundled DEMO datasets.

- All 64 districts of Bangladesh.
- Deduplicated + expanded commodity list (~80 items, realistic BD price ranges).
- Clearly synthetic prototype data (labelled "নমুনা ডেটা" in the UI).
Run from repo root:  python3 tools_gen_data.py
"""
import random
import numpy as np
import pandas as pd

rng = random.Random(42)

DISTRICTS = [
    # Dhaka division (13)
    'Dhaka', 'Gazipur', 'Narayanganj', 'Tangail', 'Kishoreganj', 'Manikganj',
    'Munshiganj', 'Narsingdi', 'Rajbari', 'Madaripur', 'Gopalganj', 'Shariatpur', 'Faridpur',
    # Chattogram division (11)
    'Chattogram', 'Coxs Bazar', 'Bandarban', 'Rangamati', 'Khagrachhari', 'Cumilla',
    'Lakshmipur', 'Noakhali', 'Feni', 'Brahmanbaria', 'Chandpur',
    # Sylhet division (4)
    'Sylhet', 'Habiganj', 'Moulvibazar', 'Sunamganj',
    # Rajshahi division (8)
    'Rajshahi', 'Bogra', 'Pabna', 'Sirajganj', 'Natore', 'Chapainawabganj', 'Naogaon', 'Joypurhat',
    # Khulna division (10)
    'Khulna', 'Jashore', 'Satkhira', 'Magura', 'Narail', 'Jhenaidah', 'Chuadanga', 'Meherpur',
    'Kushtia', 'Bagerhat',
    # Barishal division (6)
    'Barishal', 'Patuakhali', 'Barguna', 'Bhola', 'Pirojpur', 'Jhalokati',
    # Rangpur division (8)
    'Rangpur', 'Dinajpur', 'Kurigram', 'Gaibandha', 'Nilphamari', 'Panchagarh', 'Thakurgaon', 'Lalmonirhat',
    # Mymensingh division (4)
    'Mymensingh', 'Jamalpur', 'Netrokona', 'Sherpur',
]
assert len(DISTRICTS) == 64 and len(set(DISTRICTS)) == 64, len(DISTRICTS)

# Commodity -> (category, base ৳/kg typical BD level, seasonal peak months)
COMMODITIES = {
    # Foodgrains
    'Rice (Common)': ('Foodgrains', 62, [10, 11]), 'Rice (Fine/Premium)': ('Foodgrains', 95, [10, 11]),
    'Aus Rice': ('Foodgrains', 68, [11, 12]), 'Aman Rice': ('Foodgrains', 70, [12, 1]),
    'Wheat': ('Foodgrains', 55, [4, 5]), 'Bajra': ('Foodgrains', 45, []), 'Barley': ('Foodgrains', 48, []),
    'Maize': ('Foodgrains', 32, []), 'Jowar (Sorghum)': ('Foodgrains', 42, []),
    'Sugar': ('Foodgrains', 90, []), 'Molasses (Gur)': ('Foodgrains', 85, []),
    # Pulses
    'Gram (Chickpea)': ('Pulses', 105, [3, 4]), 'Mung Bean': ('Pulses', 130, [8, 9]),
    'Masoor (Lentil)': ('Pulses', 115, [3, 4]), 'Black Gram (Kalochana)': ('Pulses', 140, []),
    'Rajma (Kidney Bean)': ('Pulses', 155, []), 'Pulses (Mixed)': ('Pulses', 120, []),
    # Oilseeds / fiber
    'Mustard': ('Oilseeds', 110, [2, 3]), 'Soybean': ('Oilseeds', 85, []), 'Groundnut': ('Oilseeds', 120, []),
    'Sunflower Seed': ('Oilseeds', 95, []), 'Coconut': ('Oilseeds', 70, []), 'Oilseeds (Mixed)': ('Oilseeds', 100, []),
    'Cotton': ('Oilseeds', 75, []), 'Jute': ('Fiber', 105, [7, 8]),
    # Vegetables
    'Potato': ('Vegetable', 30, [1, 2]), 'Onion': ('Vegetable', 55, [5, 6]), 'Garlic': ('Vegetable', 220, []),
    'Tomato': ('Vegetable', 35, [11, 12]), 'Brinjal': ('Vegetable', 32, []), 'Cabbage': ('Vegetable', 28, []),
    'Cauliflower': ('Vegetable', 35, [12, 1]), 'Green Chilli': ('Vegetable', 80, []),
    'Cucumber': ('Vegetable', 30, []), 'Pumpkin': ('Vegetable', 26, []), 'Bitter Gourd': ('Vegetable', 55, []),
    'Bottle Gourd': ('Vegetable', 40, []), 'Snake Gourd': ('Vegetable', 38, []), 'Pointed Gourd': ('Vegetable', 95, []),
    'Okra (Ladies Finger)': ('Vegetable', 60, []), 'Beans (French)': ('Vegetable', 70, []),
    'Peas (Green)': ('Vegetable', 65, [12, 1]), 'Spinach': ('Vegetable', 40, []), 'Lal Shak': ('Vegetable', 35, []),
    'Radish': ('Vegetable', 30, []), 'Carrot': ('Vegetable', 45, []), 'Beet': ('Vegetable', 40, []),
    'Drumstick': ('Vegetable', 90, []), 'Kolakopa': ('Vegetable', 45, []), 'Sweet Potato': ('Vegetable', 35, []),
    'Papaya (Green)': ('Vegetable', 28, []), 'Banana (Green)': ('Vegetable', 25, []),
    # Fruits
    'Watermelon': ('Fruit', 22, [5, 6]), 'Mango': ('Fruit', 120, [6, 7]), 'Banana': ('Fruit', 45, []),
    'Jackfruit': ('Fruit', 55, [6, 7]), 'Guava': ('Fruit', 60, [11, 12]), 'Papaya': ('Fruit', 40, []),
    'Pineapple': ('Fruit', 65, [4, 5]), 'Lychee': ('Fruit', 130, [5, 6]),
    'Kamlabuk (Rose Apple)': ('Fruit', 50, [5, 6]), 'Blackberry (Jam)': ('Fruit', 80, []),
    'Orange': ('Fruit', 110, [1, 2]), 'Lemon': ('Fruit', 90, []), 'Citrus (Mixed)': ('Fruit', 100, []),
    'Pomegranate': ('Fruit', 180, []), 'Date (Khajur)': ('Fruit', 220, [9, 10]),
    'Coconut (Daan)': ('Fruit', 70, []), 'Betel Nut (Supari)': ('Fruit', 160, []),
    'Sugarcane': ('Fruit', 15, [12, 1]), 'Tea Leaves': ('Fruit', 160, []),
    # Spices
    'Red Chilli': ('Spices', 260, []), 'Turmeric': ('Spices', 180, []), 'Ginger': ('Spices', 160, [1, 2]),
    'Coriander Seed': ('Spices', 130, []), 'Cumin': ('Spices', 350, []), 'Fennel': ('Spices', 240, []),
    'Fenugreek': ('Spices', 95, []), 'Black Cumin (Kalo Jira)': ('Spices', 300, []),
    'Bay Leaf': ('Spices', 200, []), 'Cinnamon': ('Spices', 400, []), 'Cloves': ('Spices', 650, []),
    'Cardamom': ('Spices', 900, []), 'Salt': ('Spices', 30, []),
}
names = sorted(COMMODITIES.keys())
assert len(names) == len(set(names)), "duplicate commodity names!"


def region_factor(dist, cat):
    f = 1.0
    if dist in ('Bhola', 'Patuakhali', 'Barguna', 'Pirojpur', 'Satkhira', 'Khulna', 'Coxs Bazar', 'Bagerhat') \
            and cat in ('Foodgrains', 'Fruit'):
        f *= 1.06
    if dist in ('Rangpur', 'Dinajpur', 'Gaibandha', 'Kurigram', 'Panchagarh', 'Thakurgaon', 'Nilphamari', 'Lalmonirhat') \
            and cat == 'Foodgrains':
        f *= 0.95
    if dist in ('Mymensingh', 'Jamalpur', 'Netrokona', 'Sherpur', 'Tangail') and cat == 'Fruit':
        f *= 0.97
    if dist in ('Sylhet', 'Moulvibazar', 'Sunamganj', 'Habiganj') and cat == 'Fruit':
        f *= 1.04
    if dist in ('Dhaka', 'Gazipur', 'Narayanganj', 'Chattogram', 'Cumilla'):
        f *= 1.03
    return f


# ---------------- price data ----------------
start = pd.Timestamp('2025-11-01')
end = pd.Timestamp('2026-10-18')
dates = pd.date_range(start, end, freq='D')
rows = []
for dist in DISTRICTS:
    dnoise = rng.uniform(0.92, 1.08)
    markets = [f"{dist} Sadar Bazar", f"{dist} Paurashaha Bazar", f"{dist} Hat-Bazar Point"]
    for crop in names:
        cat, base, peaks = COMMODITIES[crop]
        vol = 0.06 if cat == 'Foodgrains' else 0.10
        off = rng.randrange(0, 3)
        for dt in dates[off::3]:
            mkt = markets[0] if rng.random() < 0.7 else rng.choice(markets)
            season = 1.0
            if peaks:
                mid = min(((dt.month - p) % 12) for p in peaks)
                season = 1.18 if mid == 0 else (1.10 if mid <= 2 else 0.92)
            drift = 1 + 0.10 * np.sin((dt.dayofyear / 365) * 2 * np.pi + (sum(map(ord, crop)) % 6))
            noise = rng.gauss(1.0, vol)
            price = max(1.0, round(base * dnoise * season * drift * noise * region_factor(dist, cat), 2))
            rows.append((dist, crop, mkt, dt.strftime('%Y-%m-%d'), price))
pd.DataFrame(rows, columns=['District_Name', 'Crop_Name', 'Market_Name', 'Price_Date', 'Price_Tk_kg']) \
    .to_csv('bd_crop_price_data.csv', index=False)
print('price rows:', len(rows))

# ---------------- production data ----------------
YIELD_Q_HA = {
    'Rice (Common)': 4.2, 'Rice (Fine/Premium)': 4.6, 'Aus Rice': 3.6, 'Aman Rice': 4.3, 'Wheat': 2.9,
    'Bajra': 1.6, 'Barley': 2.2, 'Maize': 4.8, 'Jowar (Sorghum)': 1.8,
    'Gram (Chickpea)': 0.95, 'Mung Bean': 0.8, 'Masoor (Lentil)': 1.1, 'Black Gram (Kalochana)': 0.8,
    'Rajma (Kidney Bean)': 1.2, 'Pulses (Mixed)': 1.0,
    'Mustard': 1.0, 'Soybean': 1.5, 'Groundnut': 1.4, 'Sunflower Seed': 1.1, 'Coconut': 8.0,
    'Oilseeds (Mixed)': 1.0, 'Cotton': 0.9, 'Jute': 2.6,
    'Potato': 20.0, 'Onion': 16.0, 'Garlic': 12.0, 'Tomato': 20.0, 'Brinjal': 18.0, 'Cabbage': 25.0,
    'Cauliflower': 20.0, 'Green Chilli': 14.0, 'Red Chilli': 8.0, 'Cucumber': 22.0, 'Pumpkin': 20.0,
    'Bitter Gourd': 15.0, 'Bottle Gourd': 18.0, 'Snake Gourd': 17.0, 'Pointed Gourd': 10.0,
    'Okra (Ladies Finger)': 8.0, 'Beans (French)': 7.0, 'Peas (Green)': 5.0, 'Spinach': 15.0,
    'Lal Shak': 14.0, 'Radish': 20.0, 'Carrot': 20.0, 'Beet': 18.0, 'Drumstick': 6.0, 'Kolakopa': 12.0,
    'Sweet Potato': 18.0, 'Papaya (Green)': 25.0, 'Banana (Green)': 22.0, 'Watermelon': 30.0,
    'Mango': 8.0, 'Banana': 30.0, 'Jackfruit': 12.0, 'Guava': 15.0, 'Papaya': 35.0, 'Pineapple': 25.0,
    'Lychee': 4.0, 'Kamlabuk (Rose Apple)': 12.0, 'Blackberry (Jam)': 8.0, 'Orange': 10.0, 'Lemon': 9.0,
    'Citrus (Mixed)': 9.0, 'Pomegranate': 6.0, 'Date (Khajur)': 5.0, 'Coconut (Daan)': 7.0,
    'Betel Nut (Supari)': 3.0, 'Sugarcane': 60.0, 'Tea Leaves': 2.2,
    'Turmeric': 12.0, 'Ginger': 15.0, 'Coriander Seed': 1.2, 'Cumin': 0.9, 'Fennel': 1.0,
    'Fenugreek': 1.1, 'Black Cumin (Kalo Jira)': 0.8,
}
prow = []
for dist in DISTRICTS:
    for crop in names:
        y = YIELD_Q_HA.get(crop)
        if not y:
            continue
        for year in (2024, 2025):
            yr_noise = rng.uniform(0.85, 1.15) * region_factor(dist, 'Yield')
            prow.append((dist, crop, f"{dist} Sadar Upazila", year, round(y * yr_noise, 2)))
pd.DataFrame(prow, columns=['District_Name', 'Crop_Name', 'Upazila_Name', 'Year', 'Yield_Quintals_per_Ha']) \
    .to_csv('bd_crop_production_data.csv', index=False)
print('prod rows:', len(prow))

# ---------------- soil data ----------------
CHAR_COAST = {'Coxs Bazar', 'Bhola', 'Patuakhali'}
SANDY_SOUTH = {'Barguna', 'Pirojpur', 'Jhalokati', 'Barishal', 'Khulna', 'Satkhira', 'Bagerhat'}
HIGHER_NORTH = {'Rangpur', 'Dinajpur', 'Panchagarh', 'Thakurgaon', 'Nilphamari', 'Lalmonirhat', 'Kurigram', 'Gaibandha'}
HC_TRACT = {'Netrokona', 'Sunamganj', 'Habiganj', 'Moulvibazar', 'Sylhet', 'Rangamati', 'Khagrachhari', 'Bandarban'}
BARIND_TRACT = {'Naogaon', 'Chapainawabganj', 'Rajshahi', 'Joypurhat', 'Bogra', 'Sirajganj'}
srow = []
for dist in DISTRICTS:
    if dist in CHAR_COAST:
        soil, ph = 'Sandy Loam', rng.uniform(6.0, 6.8)
    elif dist in SANDY_SOUTH:
        soil, ph = 'Silty Clay', rng.uniform(5.8, 6.9)
    elif dist in HIGHER_NORTH:
        soil, ph = 'Clay Loam', rng.uniform(5.5, 6.5)
    elif dist in HC_TRACT:
        soil, ph = 'Clay', rng.uniform(4.8, 5.8)
    elif dist in BARIND_TRACT:
        soil, ph = 'Loamy', rng.uniform(6.2, 7.3)
    else:
        soil, ph = 'Loamy', rng.uniform(5.9, 7.2)
    n = rng.uniform(18, 42)
    om = rng.uniform(0.8, 3.2)
    if dist in HC_TRACT:
        om = rng.uniform(2.2, 4.5)
    if dist in HIGHER_NORTH:
        n = rng.uniform(25, 48)
    srow.append((dist, soil, round(ph, 2), round(n, 1), round(rng.uniform(8, 26), 1),
                 round(rng.uniform(12, 38), 1), round(om, 1), round(rng.uniform(0.15, 0.9), 2)))
pd.DataFrame(srow, columns=['District_Name', 'Soil_Type', 'pH_Level', 'Nitrogen_Content_kg_ha',
                            'Phosphorus_Content_kg_ha', 'Potassium_Content_kg_ha',
                            'Organic_Matter_Percent', 'Moisture_Percent']) \
    .to_csv('bd_soil_analysis_data.csv', index=False)
print('soil rows:', len(srow))
