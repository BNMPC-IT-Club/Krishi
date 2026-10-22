"""Rule-based, Bangladesh-relevant guidance for the inherited 38-class model.

Chemical recommendations are deliberately allow-listed: a product is shown only
when the DAE Pesticide Information Repository has a registration number and an
explicit crop/pest-use record. The repository is not a live stock feed. No AI
output is used to invent pesticide brands, doses, or water amounts.
"""
from __future__ import annotations

from typing import Any

from backend.disease_labels import DISEASE_TRANSLATION

CHECKED_ON = "2026-10-22"
DAE_REGISTRY_URL = "https://dae.gov.bd/site/files/4ea8e032-77df-4e6b-952b-5eab3004113c/-Registered-Pesticide"
PPW_REPOSITORY_URL = "https://ppw.krishi.gov.bd/"
PRISM_LOCAL_LIST_URL = "https://prism.dae.gov.bd/pesticide-list"
DAE_LABEL_LAW_URL = "https://dae.gov.bd/pages/notices/6922f1ecdbfbab28ce0d6c95"

_BASE_SOURCES = [
    {"label": "DAE Pesticide Information Repository (PPW)", "url": PPW_REPOSITORY_URL},
    {"label": "DAE PRISM: উপজেলা-ভিত্তিক বাজারজাত পণ্যের তালিকা", "url": PRISM_LOCAL_LIST_URL},
    {"label": "DAE: বালাইনাশকের লেবেল ব্যবহারের নির্দেশনা", "url": DAE_LABEL_LAW_URL},
]

# These are labels to compare against the plant, not symptoms the classifier
# claims it has actually observed in the uploaded photo.
SIGNS_TO_CHECK: dict[str, str] = {
    "Apple___Apple_scab": "পাতা বা ফলে জলপাই-বাদামি, খসখসে দাগ আছে কি দেখুন।",
    "Apple___Black_rot": "পাতা বা ফলে বাদামি/কালচে পচা দাগ এবং ফল শুকিয়ে যাওয়ার লক্ষণ মিলিয়ে দেখুন।",
    "Apple___Cedar_apple_rust": "পাতার ওপর কমলা-হলুদ দাগ বা নিচে গঠন আছে কি দেখুন।",
    "Cherry_(including_sour)___Powdery_mildew": "পাতা বা কচি ডগায় সাদা গুঁড়ার মতো আস্তরণ আছে কি দেখুন।",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "ভুট্টার পাতায় শিরার সঙ্গে লম্বা ধূসর/বাদামি দাগ আছে কি দেখুন।",
    "Corn_(maize)___Common_rust_": "পাতায় ছোট, উঁচু, লালচে-বাদামি গুঁড়ার ফোস্কার মতো দাগ আছে কি দেখুন।",
    "Corn_(maize)___Northern_Leaf_Blight": "পাতায় লম্বা, ধূসর-সবুজ, পরে বাদামি হওয়া দাগ আছে কি দেখুন।",
    "Grape___Black_rot": "আঙুরের পাতা বা ফলে গাঢ় দাগ ও ফলের কালো পচন মিলিয়ে দেখুন।",
    "Grape___Esca_(Black_Measles)": "পাতায় শিরার মাঝখানে হলুদ/লালচে অংশ, শুকনো ডাল বা ফলে কালো দাগ আছে কি দেখুন।",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "পাতায় অনিয়মিত বাদামি দাগ এবং হলদে কিনারা আছে কি দেখুন।",
    "Orange___Haunglongbing_(Citrus_greening)": "নতুন পাতায় অসমান হলদে দাগ, ছোট/বিকৃত ফল বা এক পাশের ডাল শুকানো আছে কি দেখুন।",
    "Peach___Bacterial_spot": "পাতা/ফলে ছোট গাঢ় দাগ, হলুদ কিনারা বা ফলের ক্ষত আছে কি দেখুন।",
    "Pepper,_bell___Bacterial_spot": "ক্যাপসিকামের পাতা বা ফলে ছোট জলভেজা/গাঢ় দাগ আছে কি দেখুন।",
    "Potato___Early_blight": "আলুর পুরোনো পাতায় গোল বাদামি দাগের ভেতর বলয় আছে কি দেখুন।",
    "Potato___Late_blight": "আলুর পাতায় দ্রুত বাড়তে থাকা জলভেজা কালচে দাগ, বিশেষত পাতার নিচে সাদা আবরণ আছে কি দেখুন।",
    "Squash___Powdery_mildew": "স্কোয়াশের পাতায় মুছে না-যাওয়া সাদা গুঁড়ার মতো দাগ আছে কি দেখুন।",
    "Strawberry___Leaf_scorch": "স্ট্রবেরির পাতায় ছোট বেগুনি/লালচে দাগ, পরে বাদামি কেন্দ্র আছে কি দেখুন।",
    "Tomato___Bacterial_spot": "টমেটোর পাতা/ফলে ছোট জলভেজা থেকে গাঢ় দাগ আছে কি দেখুন।",
    "Tomato___Early_blight": "টমেটোর পুরোনো পাতায় গোল বাদামি দাগের ভেতর বলয় আছে কি দেখুন।",
    "Tomato___Late_blight": "টমেটোর পাতায় দ্রুত বাড়তে থাকা জলভেজা কালচে দাগ, বিশেষত পাতার নিচে সাদা আবরণ আছে কি দেখুন।",
    "Tomato___Leaf_Mold": "টমেটো পাতার ওপর ফ্যাকাশে দাগ এবং নিচে জলপাই-সবুজ ছাঁচ আছে কি দেখুন।",
    "Tomato___Septoria_leaf_spot": "পাতায় অনেক ছোট গোল দাগ, গাঢ় কিনারা ও ফিকে কেন্দ্র আছে কি দেখুন।",
    "Tomato___Spider_mites Two-spotted_spider_mite": "পাতার নিচে সূক্ষ্ম জাল, চলমান ক্ষুদ্র মাকড় বা ছোট ফ্যাকাশে বিন্দু আছে কি দেখুন।",
    "Tomato___Target_Spot": "টমেটোর পাতায় গোল বাদামি দাগ ও একাধিক বলয় আছে কি দেখুন।",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "নতুন পাতা কুঁকড়ে/হলদে হওয়া ও গাছ খাটো হয়ে যাওয়ার লক্ষণ মিলিয়ে দেখুন।",
    "Tomato___Tomato_mosaic_virus": "পাতায় হালকা-গাঢ় সবুজ মোজাইক ছোপ বা বিকৃতি আছে কি দেখুন।",
}

# Product/label information transcribed from DAE's Pesticide Information
# Repository records. Keep rates and crop/pest scope attached to the exact AP
# registration; never generalize a rate to another product or crop.
ACROBAT_MZ = {
    "name": "Acrobat MZ",
    "registration_no": "AP-353",
    "active_ingredients": "Mancozeb + Dimethomorph",
    "label_scope": "আলু — Early blight ও Late blight",
    "rate": "৪ গ্রাম / ১ লিটার পানি",
    "directions": [
        "DAE repository-তে প্রাথমিক সংক্রমণের পর্যায়ে ব্যবহারের কথা আছে; প্রয়োজন হলে ২ সপ্তাহ পর পুনঃপ্রয়োগের নির্দেশও আছে।",
        "রেকর্ডে স্প্রে-পরবর্তী ফসল তোলার বিরতি ৭–১৪ দিন বলা আছে; প্যাকেটের বর্তমান লেবেলই চূড়ান্ত।",
    ],
    "source_label": "DAE PPW product record — Acrobat MZ",
    "source_url": "https://ppw.krishi.gov.bd/pesticide-details/11633",
}

CABRIO_TOP = {
    "name": "Cabrio Top",
    "registration_no": "AP-1770",
    "active_ingredients": "Pyraclostrobin + Metiram",
    "label_scope": "কুমড়াজাতীয় (Cucurbits) — Powdery mildew",
    "rate": "৩ গ্রাম / ১ লিটার পানি",
    "directions": [
        "DAE PPW record-এ রোগের আগেই বা রোগের প্রাথমিক পর্যায়ে প্রয়োগের কথা আছে; ব্যবহারের আগে প্যাকেটের লেবেলে আপনার নির্দিষ্ট কুমড়াজাতীয় ফসলটি আছে কি না মিলিয়ে নিন।",
        "রেকর্ডে প্রয়োগের পর ৭–১৪ দিন ফসল না তোলার কথা আছে; প্যাকেটের বর্তমান লেবেলই চূড়ান্ত।",
    ],
    "source_label": "DAE PPW product record — Cabrio Top",
    "source_url": "https://ppw.krishi.gov.bd/pesticide-details/4522",
}

_PRODUCT_BY_CLASS: dict[str, list[dict[str, Any]]] = {
    "Potato___Early_blight": [ACROBAT_MZ],
    "Potato___Late_blight": [ACROBAT_MZ],
    "Squash___Powdery_mildew": [CABRIO_TOP],
}


def _watering_guidance(class_label: str) -> dict[str, str]:
    crop = class_label.split("___", 1)[0]
    if crop in {"Potato", "Tomato", "Corn_(maize)"}:
        care = (
            "মাটির আর্দ্রতা দেখে গোড়ায় সেচ দিন; পাতার ওপর পানি ছিটানো ও জলাবদ্ধতা এড়ান, "
            "পানি নিষ্কাশনের পথ খোলা রাখুন। ভেজা/কুয়াশাচ্ছন্ন আবহাওয়ায় অতিরিক্ত সেচ দেবেন না।"
        )
    else:
        care = (
            "মাটির আর্দ্রতা দেখে গোড়ায় প্রয়োজনমতো সেচ দিন; পাতায় পানি জমিয়ে রাখা ও "
            "জলাবদ্ধতা এড়ান।"
        )
    return {
        "care": care,
        "amount_note": (
            "এই ছবি থেকে জমির আয়তন, মাটির ধরন/আর্দ্রতা, গাছের বয়স ও আবহাওয়া জানা যায় না—"
            "তাই নিরাপদে নির্দিষ্ট লিটার/বিঘা বলা সম্ভব নয়।"
        ),
    }


def _general_actions(class_label: str) -> tuple[str, list[str], str]:
    """Return (category, practical steps, product note) for uncurated classes."""
    if "___healthy" in class_label:
        return (
            "healthy_class",
            [
                "পাতার দুই পাশ ও নতুন পাতায় লক্ষণ আছে কি নিয়মিত দেখুন; ছবির ‘healthy’ শ্রেণি রোগমুক্তির নিশ্চয়তা নয়।",
                "লক্ষণ না মিললে শুধু মডেল-স্কোরের কারণে স্প্রে/ওষুধ দেবেন না।",
            ],
            "কোনো ওষুধ প্রয়োজন বলে এই ফল প্রমাণ করে না; প্রতিরোধমূলকভাবে বালাইনাশক দেবেন না।",
        )

    if "Virus" in class_label or "Citrus_greening" in class_label:
        return (
            "possible_viral_or_greening",
            [
                "নতুন পাতার কুঁকড়ানো, মোজাইক/অসমান হলদে ভাব এবং আক্রান্ত গাছের বিস্তার হাতে মিলিয়ে দেখুন।",
                "ভাইরাসে ছত্রাকনাশক সারায় না। লক্ষণ নিশ্চিত হলে আক্রান্ত গাছ/চারা আলাদা রাখুন; বাহক পোকা চোখে পড়লে ফসল-লেবেলমাফিক ব্যবস্থা নিন।",
                "সরঞ্জাম ও হাত পরিষ্কার রাখুন; রোগাক্রান্ত গাছের বংশবিস্তার/চারা তৈরি করবেন না।",
            ],
            "ভাইরাসের জন্য নিরাময়কারী স্প্রে নেই; বাহক পোকা নিশ্চিত না হলে কীটনাশক দেবেন না।",
        )

    if "Bacterial" in class_label:
        return (
            "possible_bacterial",
            [
                "পাতার দুই পাশ, কাণ্ড ও ফলেও একই রকম দাগ আছে কি মিলিয়ে দেখুন; অন্য গাছেও ছড়াচ্ছে কি লক্ষ্য করুন।",
                "ভেজা গাছে হাত দেওয়া/ছাঁটাই এড়ান; ব্যবহারের পর সরঞ্জাম পরিষ্কার করুন এবং আক্রান্ত অবশেষ জমিতে ফেলে রাখবেন না।",
                "রোগের লক্ষণ নিশ্চিত হওয়ার আগে অ্যান্টিবায়োটিক বা তামাযুক্ত স্প্রে অনুমান করে ব্যবহার করবেন না।",
            ],
            "এই ছবির মডেল-লেবেল একা ব্যাকটেরিয়াল রোগ নিশ্চিত করে না; ফসল ও রোগের নির্দিষ্ট DAE label match না থাকায় পণ্য/মাত্রা দেখানো হচ্ছে না।",
        )

    if "Spider_mites" in class_label:
        return (
            "possible_mite",
            [
                "পাতার নিচে মাকড়, সূক্ষ্ম জাল ও ক্ষুদ্র চলমান দাগ হাতে/আতশকাচে নিশ্চিত করুন।",
                "আক্রান্ত গাছ আলাদা পর্যবেক্ষণ করুন; অল্প আক্রান্ত পাতা জমিতে না ফেলে সরিয়ে ফেলুন।",
                "মাকড় নিশ্চিত না হলে কীটনাশক/মাকড়নাশক দেবেন না; ভুল পণ্য উপকারী পোকাও মেরে ফেলতে পারে।",
            ],
            "টমেটো ও Spider mite—এই দুইয়ের জন্য বর্তমান, স্পষ্ট DAE label match যাচাই না হওয়ায় নির্দিষ্ট পণ্য/মাত্রা দেওয়া হচ্ছে না।",
        )

    if class_label == "Tomato___Early_blight":
        return (
            "possible_leaf_disease",
            [
                "টমেটোর পুরোনো পাতায় গোল বাদামি বলয়যুক্ত দাগ আছে কি হাতে মিলিয়ে দেখুন; অন্য রোগ/পুষ্টিঘাটতির লক্ষণও বাদ দিন।",
                "আক্রান্ত পাতা জমিতে না ফেলে সরিয়ে দিন, পাতায় দীর্ঘসময় পানি লাগা কমান এবং গাছের মাঝে বাতাস চলাচল রাখুন।",
                "স্প্রে করার আগে ফসল ও রোগের সঙ্গে পণ্যের বর্তমান লেবেল মিলিয়ে উপজেলা কৃষি অফিসারের পরামর্শ নিন।",
            ],
            "DAE repository-তে এই রোগের জন্য একটি পণ্য-ব্যবহার এন্ট্রি আছে, কিন্তু formulation/লেবেল নির্দেশের বর্তমান মিল স্বাধীনভাবে নিশ্চিত করা যায়নি; তাই ব্র্যান্ড ও মাত্রা দেখানো হচ্ছে না।",
        )

    return (
        "possible_leaf_disease",
        [
            "পাতার ওপর-নিচ, কাণ্ড এবং গাছের একাধিক অংশে লক্ষণ মিলিয়ে দেখুন; পাশের সুস্থ গাছের সঙ্গে তুলনা করুন।",
            "আক্রান্ত/ঝরা পাতা জমিতে ফেলে রাখবেন না; গাছের মাঝে বাতাস চলাচল ও পানি নিষ্কাশন বজায় রাখুন।",
            "ছবির শ্রেণি নিশ্চিত রোগ নয়—ফসল, লক্ষণ ও পণ্যের label একসাথে না মিললে বালাইনাশক প্রয়োগ করবেন না।",
        ],
        "এই crop–disease জুটির জন্য স্পষ্ট, যাচাইযোগ্য DAE নিবন্ধিত product-use match না থাকায় কোনো পণ্য বা ডোজ সুপারিশ করা হচ্ছে না।",
    )


def get_disease_guidance(class_label: str) -> dict[str, Any]:
    """Return deterministic advice for one of the model's exact class labels."""
    healthy = "___healthy" in class_label
    category, actions, product_note = _general_actions(class_label)
    products = _PRODUCT_BY_CLASS.get(class_label, [])
    if products:
        category = "possible_disease_with_verified_label"
        product_note = (
            "নীচে DAE PPW-এর repository record-এ AP নম্বরসহ নির্দিষ্ট ফসল–বালাই ব্যবহারের তথ্য আছে। "
            "এটি সক্রিয় নিবন্ধন বা আপনার এলাকার দোকানের মজুতের নিশ্চয়তা নয়। কেনার আগে আসল প্যাকেটের বর্তমান "
            "লেবেলে একই ফসল ও রোগ, মাত্রা, ফসল তোলার বিরতি (PHI) এবং নিরাপত্তা নির্দেশনা মিলিয়ে নিন।"
        )
    elif not healthy:
        product_note += " স্থানীয়ভাবে অনুমোদিত পণ্য বাছতে DAE PRISM-এর উপজেলা-ভিত্তিক তালিকা দেখুন।"

    signs = SIGNS_TO_CHECK.get(
        class_label,
        "এই শ্রেণির পরিচিত লক্ষণ পাতার দুই পাশ, কাণ্ড ও নতুন পাতায় হাতে মিলিয়ে দেখুন।",
    )
    if healthy:
        reason = (
            "মডেলের শীর্ষ শ্রেণি ‘সুস্থ’; এটি প্রশিক্ষণ-শ্রেণির অনুমান, "
            "পরীক্ষিত রোগমুক্তির নিশ্চয়তা নয়।"
        )
    else:
        display_label = DISEASE_TRANSLATION.get(
            class_label, class_label.replace("___", " — ").replace("_", " ")
        )
        reason = (
            f"মডেল এই ছবির সম্ভাব্য শ্রেণি হিসেবে ‘{display_label}’ দিয়েছে। "
            "মডেল ছবিটি থেকে নির্দিষ্ট লক্ষণ ব্যাখ্যা করে না; নিচের লক্ষণগুলো হাতে মিলিয়ে দেখুন।"
        )

    sources = list(_BASE_SOURCES)
    for product in products:
        sources.append({"label": product["source_label"], "url": product["source_url"]})

    return {
        "category": category,
        "reason": reason,
        "signs_to_check": signs,
        "actions": actions,
        "product_note": product_note,
        "products": products,
        "watering": _watering_guidance(class_label),
        "source_checked_on": CHECKED_ON,
        "sources": sources,
    }
