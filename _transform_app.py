#!/usr/bin/env python3
"""One-shot transformation of app.py -> Smart Krishi Buddhimotta.

Applies surgical block replacements (verified boundaries) so the existing
Streamlit architecture is preserved while removing broken/dead code
(TensorFlow model, Gemini, mock auth, SMS/Mongo), switching to the PyTorch
ResNet9 disease model, Open-Meteo weather, Groq AI chat and honest
sample-data labelling for market prices/forecasts.
"""

PATH = "app.py"
lines = open(PATH, encoding="utf-8").read().split("\n")


def rep(start_1based, end_1based, new_text):
    """Replace lines [start..end] inclusive (1-based) with new_text."""
    return (start_1based - 1, end_1based, new_text.rstrip("\n").split("\n"))


EDITS = []

# ---- 1. Header imports: drop gemini/tf/mongo/twilio; add torch/PIL/cv2 + modules
EDITS.append(rep(13, 47, '''import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from PIL import Image, ImageOps
import cv2
import torch

# Project modules (kept separate so identifiers/model classes stay stable)
from disease_model import load_resnet9, predict_torch, CLASS_LABELS, WEIGHTS_FILE
from weather_openmeteo import (DISTRICT_COORDS, get_current_weather, get_forecast,
                               weather_code_info, farm_advice)
from groq_assistant import chat_completion, get_groq_key
import dam_market'''))

# ---- 2. Model loading: cached PyTorch ResNet9 instead of broken Keras .h5
EDITS.append(rep(49, 59, '''@st.cache_resource(show_spinner=False)
def load_plant_model():
    """Load the pretrained PyTorch ResNet9 once per session (no retraining)."""
    try:
        return load_resnet9(WEIGHTS_FILE)
    except Exception as e:
        print(f"Disease model load error: {e}")
        return None'''))

# ---- 3. Page config + Bengali font + professional theme (rebrand)
EDITS.append(rep(111, 121, '''# -----------------------------------------------------------------------------
# 1. APP CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart Krishi Buddhimotta | স্মার্ট কৃষি বুদ্ধিমত্তা",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Bengali-first typography (Hind Siliguri with safe fallbacks)
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)'''))

# ---- 4. Replace MongoDB/mock-auth DB section with honest sample-data loader
EDITS.append(rep(352, 403, '''# -----------------------------------------------------------------------------
# 2. DATA LOADING (bundled dataset is SAMPLE data — never shown as live prices)
# -----------------------------------------------------------------------------'''))

# ---- 5. Rewrite load_data + remove OpenWeatherMap/Gemini helpers
EDITS.append(rep(405, 551, '''@st.cache_data(show_spinner=False)
def load_data():
    try:
        price_df = pd.read_csv('bd_crop_price_data.csv')
        prod_df = pd.read_csv('bd_crop_production_data.csv')
        soil_df = pd.read_csv('bd_soil_analysis_data.csv')
        price_df['Price_Date'] = pd.to_datetime(price_df['Price_Date'])
        return price_df, prod_df, soil_df
    except FileNotFoundError:
        return None, None, None

price_df, prod_df, soil_df = load_data()

SAMPLE_DATA_NOTICE = (
    "⚠️ **নমুনা ডেটা (ডেমো):** এই খাতের দামগুলো একটি সংকলিত নমুনা ডেটাসেট থেকে নেওয়া "
    "এবং এগুলো **আজকের বাস্তব বাজারদর নয়**। প্রতিটি পর্যবেক্ষণের তারিখ উল্লেখ করা আছে। "
    "বাস্তব দামের জন্য কৃষি সম্প্রসারণ অধিদপ্তর (ডিএই) বা স্থানীয় বাজার কর্তৃপক্ষের কাছ থেকে "
    "তথ্য নিয়ে CSV হিসেবে আপলোড করুন।"
)'''))

# ---- 6. Remove mock authentication block entirely (misleading feature)
EDITS.append(rep(1140, 1201, '''# -----------------------------------------------------------------------------
# 4. (Removed) Mock login system — it was in-memory only and gave a false
#    sense of security, so it has been taken out per an honest-UI policy.
# -----------------------------------------------------------------------------'''))

# ---- 7. Remove Twilio SMS helper (optional paid service no longer used)
EDITS.append(rep(1225, 1238, '''# (Removed) send_sms_alert / Twilio integration — required paid credentials and
# was non-functional in the free setup.'''))

# ---- 8. Honest forecast guardrails inside predict_next_30_days
EDITS.append(rep(1283, 1284, '''    if len(filtered_df) < 10:
        return None, None, None

    # Honesty guard: bundled dataset is sample data and forecasts are
    # experimental — results must always be labelled as such by the caller.
    last_obs = filtered_df['Price_Date'].max()
    if (datetime.datetime.now() - last_obs.to_pydatetime()).days > 120:
        # Too old to present even as an experimental projection
        return None, None, None'''))

# ---- 9. New MENU options (add dashboard/weather/AI/about pages)
EDITS.append(rep(1443, 1444, '''MENU_OPTIONS = ["🏠 ড্যাশবোর্ড", "💰 আজকের বাজারদর", "📊 মূল্য পূর্বাভাস (এআই)", "🦠 ফসলের রোগ শনাক্তকরণ", "🌦️ আবহাওয়া", "🤖 কৃষি সহায়ক AI", "🌱 মাটি ও ফসল পরামর্শদাতা", "ℹ️ প্রকল্প সম্পর্কে"]
MENU_ICONS = ["house", "shop", "graph-up-arrow", "bug", "cloud-sun", "robot", "flower1", "info-circle"]'''))

# ---- 10. Sidebar header rebrand
EDITS.append(rep(1504, 1504, '''st.sidebar.markdown("**স্মার্ট কৃষি বুদ্ধিমত্তা**  \\n*Smart Krishi Buddhimotta*\n\n🇧🇩 বাংলাদেশের কৃষকদের জন্য এআই-চালিত সহায়ক প্ল্যাটফর্ম")'''))

# ---- 12. Disease detection module rewrite (PyTorch inference + Bangla results)
EDITS.append(rep(2105, 2243, '''elif menu == "🦠 ফসলের রোগ শনাক্তকরণ":
    st.title("🦠 ফসলের রোগ শনাক্তকরণ")
    st.markdown(
        "AI মডেলের বিশ্লেষণের জন্য ফসলের পাতার একটি স্পষ্ট ছবি তুলুন বা আপলোড করুন। "
        "মডেলটি **৩৮টি শ্রেণির** (আলু, টমেটো, ভুট্টা, আঙুর, পেয়ারা/জাম, মরিচ, স্ট্রবেরি ইত্যাদি) "
        "মধ্যে থেকে রোগ শনাক্ত করে। এটি শুধু প্রাথমিক দিকনির্দেশনা — চূড়ান্ত সিদ্ধান্তে "
        "স্থানীয় কৃষি অফিসের পরামর্শ নিন।"
    )

    model = load_plant_model()
    if not model:
        st.error("রোগ শনাক্তকরণ মডেল (`plant_disease_weights.pth`) পাওয়া যায়নি বা লোড করা যায়নি। "
                 "ফাইলটি রেপোতে আছে কিনা দেখুন (Git LFS হলে ডাউনলোড নিশ্চিত করুন)।")
        st.stop()

    tab_cam, tab_up = st.tabs(["📸 ছবি তুলুন", "📂 ছবি আপলোড করুন"])

    img_file = None
    with tab_cam:
        cam_img = st.camera_input("ফসল বা পাতার ছবি তুলুন")
        if cam_img:
            img_file = cam_img
    with tab_up:
        up_img = st.file_uploader("গ্যালারি থেকে ছবি নির্বাচন করুন (JPG/PNG, ≤৮MB)",
                                  type=["jpg", "jpeg", "png"], key="disease_upload")
        if up_img:
            img_file = up_img

    if img_file:
        try:
            file_bytes = np.asarray(bytearray(img_file.getvalue()), dtype=np.uint8) \
                if hasattr(img_file, "getvalue") else None
            image = Image.open(img_file if file_bytes is None else io.BytesIO(file_bytes))
            image = image.convert("RGB")
        except Exception:
            st.error("ছবিটি পড়া যায়নি — ক্ষতিগ্রস্ত ফাইল হতে পারে। অন্য ছবি দিয়ে চেষ্টা করুন।")
            st.stop()

        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(image, caption="আপনার আপলোড করা ছবি", use_container_width=True)

        # Gentle sanity check (does not reject ordinary leaf photos)
        is_leaf, msg = is_likely_leaf(image)
        if not is_leaf:
            st.warning(msg)
            st.info("টিপস: দিনের আলোতে পাতার কাছে গিয়ে স্পষ্ট ছবি তুলুন।")

        with st.spinner("রোগ নির্ণয় চলছে..."):
            try:
                img_resized = image.resize((256, 256), Image.Resampling.LANCZOS)
                arr = np.asarray(img_resized, dtype="float32") / 255.0
                tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
                probs = predict_torch(model, tensor)
                pred_idx = int(np.argmax(probs))
                conf_score = float(probs[pred_idx] * 100)
                pred_class = CLASS_LABELS[pred_idx]
            except Exception as e:
                st.error(f"বিশ্লেষণে সমস্যা হয়েছে: {e}")
                st.stop()

        bn_label = DISEASE_TRANSLATION.get(pred_class, pred_class)
        crop_en, _, disease_en = pred_class.partition("___")
        crop_bn = CROP_BN_DISPLAY.get(crop_en.replace("_", " ").strip(", "), crop_en)

        st.divider()
        st.subheader("📋 ফলাফল")
        st.markdown(f"**ফসল (মডেলের অনুমান):** {crop_bn}  \\n**শনাক্ত অবস্থা:** ", unsafe_allow_html=True)
        if "healthy" in pred_class.lower():
            st.success(f"✅ {bn_label}")
        else:
            st.error(f"⚠️ শনাক্ত রোগ: {bn_label}")

        st.write(f"**আস্থা (Confidence):** {conf_score:.1f}%")
        st.progress(min(int(conf_score), 100) / 100)

        top3 = np.argsort(-probs)[:3]
        st.caption("সম্ভাব্য তিনটি ফলাফল:")
        for t in top3:
            st.caption(f"– {DISEASE_TRANSLATION.get(CLASS_LABELS[t], CLASS_LABELS[t])} "
                       f"({probs[t]*100:.1f}%)")

        if conf_score < 50:
            st.warning("🔎 মডেলের আস্থা কম। ছবিটি আবার তোলা বা বিশেষজ্ঞের পরামর্শ নেওয়া ভালো।")

        st.info("🌱 **অর্থ ও পরবর্তী পদক্ষেপ:** এই ফলাফল মডেলের গাণিতিক অনুমান, নিশ্চিত রোগবিজ্ঞান নয়। "
                "রোগ দেখা গেলে affected পাতা সরিয়ে ফেলুন, জৈব/রাসায়নিক ব্যবহারের আগে কৃষি সম্প্রসারণ "
                "অফিস বা উপজেলা কৃষি অফিসারের সাথে যোগাযোগ করুন।")

        # --- AI Doctor prescription (rule-based, from inherited map) ---
        st.markdown("### 💊 সাধারণ করণীয় (প্রেসক্রিপশন)")
        prescription = CROP_PRESCRIPTION_MAP.get(pred_class)
        if "healthy" in pred_class.lower():
            st.info(GENERIC_REMEDIES["healthy"])
        elif prescription:
            st.markdown(f"""
<div style="background-color:#f1f8e9;border:2px solid #81c784;border-radius:10px;padding:20px;">
<h4 style="color:#2e7d32;margin-top:0;">📋 ব্যবস্থাপত্র</h4>
<p><strong>🔍 কারণ:</strong> {prescription['cause']}</p>
<p><strong>🛡️ প্রতিকার:</strong> {prescription['solution']}</p>
<p><strong>💊 প্রস্তাবিত ঔষধ:</strong> {prescription['medicine']}</p>
<p><strong>⚖️ মাত্রা:</strong> {prescription['dosage']}</p>
<p style="font-size:.85em;color:#666;font-style:italic;">ঔষধের গায়ে লেখা নির্দেশনা মেনে সুরক্ষা পোশাক পরিধান করুন।</p>
</div>""", unsafe_allow_html=True)
        else:
            fallback = (GENERIC_REMEDIES['bacterial'] if 'bacterial' in pred_class.lower()
                        else GENERIC_REMEDIES['viral'] if 'virus' in pred_class.lower()
                        else GENERIC_REMEDIES['fungal'])
            st.warning(f"নির্দিষ্ট পরামর্শ ডেটাবেসে নেই। সাধারণ ধারণা: {fallback}")

        with st.expander("⚠️ সীাবদ্ধতা ও দাবিত্যাগ"):
            st.markdown(
                "- মডেলটি **New Plant Diseases Dataset (Kaggle)**-এ প্রশিক্ষিত — বাংলাদেশি সব ফসল/রোগ এতে নেই।\\n"
                "- যে ফসলের ছবি মডেল জানে না, সেটির জন্যও কোনো-একটি ফলাফল দেখাতে পারে — তাই ফসলের নাম মিলিয়ে নিন।\\n"
                "- রাসায়নিক সিদ্ধান্তের আগে কৃষি বিশেষজ্ঞের নিশ্চিত মতামত নিন।")'''))

# ---- 13. Footer rebrand + honest attribution
EDITS.append(rep(2378, 2379, '''# Footer
st.markdown(
    "<br><hr><div style='text-align:center;color:#555;font-size:0.9rem;'>"
    "🌾 <b>Smart Krishi Buddhimotta</b> (স্মার্ট কৃষি বুদ্ধিমত্তা) — Agri-Smart BD-এর "
    "রূপান্তরিত ও উন্নত সংস্করণ। আবহাওয়া: Open-Meteo · AI: Groq · "
    "রোগ মডেল: Kaggle New Plant Diseases Dataset (ResNet9)।"
    "</div>", unsafe_allow_html=True)'''))

# Apply edits bottom-up so line numbers stay valid
EDITS.sort(key=lambda e: e[0], reverse=True)
for start, end, new_lines in EDITS:
    lines[start:end] = new_lines

src = "\n".join(lines)

# ---- Targeted small string swaps (safe, unique) ----
swaps = [
    ('st.title("🌾 Agri-Smart BD")',
     'st.title("🌾 Smart Krishi Buddhimotta")\nst.caption("স্মার্ট কৃষি বুদ্ধিমত্তা — বাংলাদেশের কৃষকদের জন্য এআই সহায়ক")'),
    ('if menu == "📊 মূল্য পূর্বাভাস (এআই)":',
     'if menu == "📊 মূল্য পূর্বাভাস (এআই)" or menu == "💰 আজকের বাজারদর":'),
    ('elif menu == "🦠 ফসল বিষাক্তি পরিচিতি":', 'elif menu == "__REMOVED__":'),
    ('elif menu == "💰 সেরা বাজার খুঁজুন":', 'elif menu == "__REMOVED_MARKET__":'),
    # honest labelling inside price forecast page
    ('st.title("💰 সেরা বাজার খুঁজুন")', 'st.title("💰 সেরা বাজার খুঁজুন")'),
    # remove now-unused helpers that reference deleted imports
    ('def voice_to_text(audio_bytes):', 'def voice_to_text(audio_bytes):\n    return None  # voice input removed with mic recorder\n'),
    ('st.session_state.user = None\n', ''),
]
for old, new in swaps:
    if old in src and new != old:
        src = src.replace(old, new, 1)

# Insert the new pages module before the footer block
new_pages = open("_new_pages.py", encoding="utf-8").read().strip("\n")
FOOTER_MARK = "# Footer\nst.markdown("
idx = src.find(FOOTER_MARK)
assert idx != -1, "footer marker not found"
src = src[:idx] + new_pages + "\n\n" + src[idx:]

open(PATH, "w", encoding="utf-8").write(src)
print("Applied", len(EDITS), "block edits + swaps + new pages")
