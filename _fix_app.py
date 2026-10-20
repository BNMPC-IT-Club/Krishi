#!/usr/bin/env python3
"""Second-pass fixes on transformed app.py."""
src = open("app.py", encoding="utf-8").read()

# 1. Add missing imports (io, streamlit_js_eval)
old_imp = "import warnings\nwarnings.filterwarnings(\"ignore\", category=FutureWarning)\n\nfrom PIL import Image, ImageOps"
new_imp = "import io\nimport warnings\nwarnings.filterwarnings(\"ignore\", category=FutureWarning)\n\nfrom streamlit_js_eval import streamlit_js_eval\nfrom PIL import Image, ImageOps"
assert old_imp in src, "import anchor missing"
src = src.replace(old_imp, new_imp, 1)

# 2. Define CROP_BN_DISPLAY right after DISEASE_TRANSLATION dict start fallback
anchor = "GENERIC_REMEDIES = {"
crop_bn = '''CROP_BN_DISPLAY = {
    "Alu": "আলু", "Aloo": "আলু", "Tomato": "টমেটো", "Corn": "ভুট্টা", "Maize": "ভুট্টা",
    "Grapes": "আঙুর", "Apple": "সেব", "Pear": "নাশপাতি", "Bell pepper": "ক্যাপসিকাম",
    "Cherry": "চেরি", "Peach": "পীচ", "Potato": "আলু", "Strawberry": "স্ট্রবেরি",
}
''' + anchor
assert anchor in src
src = src.replace(anchor, crop_bn, 1)

# 3. Initialize session_state.user to None (legacy code references it; auth removed)
anchor2 = "if price_df is None:"
init_user = "# Legacy login was removed (in-memory mock); keep key defined so old code paths are safe.\nif 'user' not in st.session_state:\n    st.session_state.user = None\n\n" + anchor2
assert anchor2 in src
src = src.replace(anchor2, init_user, 1)

open("app.py", "w", encoding="utf-8").write(src)
print("pass-2 fixes applied")
