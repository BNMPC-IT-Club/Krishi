import re
src = open("app.py", encoding="utf-8").read()

# --- 1. Remove mic_recorder voice blocks (4 occurrences) using regex on the block structure ---
pat = re.compile(
    r"[ \t]*# Voice Input[^\n]*\n"                       # comment line
    r"(?:.*\n)*?"                                          # up to...
    r"[ \t]*audio = mic_recorder\(.*?\)\n",                # the mic line
    re.M)
# Instead of greedy regex, do targeted removals per page by locating each "# Voice Input" and its following block end markers.

def remove_voice_block(text, start_needle, end_needle, label):
    i = text.find(start_needle)
    assert i != -1, "start missing " + label
    j = text.find(end_needle, i)
    assert j != -1, "end missing " + label
    return text[:i] + text[j:]

# forecast page: from "# Voice Input" to "# Legacy Geolocation logic removed"
src = remove_voice_block(src, "    # Voice Input\n    c1, c2 = st.columns([1, 4])\n    with c1:\n        audio = mic_recorder(start_prompt=\"🎤 বলুন\", stop_prompt=\"🛑 থামুন\", key='recorder', format=\"wav\", use_container_width=True)", "    # Legacy Geolocation logic removed", "forecast")
# best market page (dead branch anyway): remove from its Voice Input to next unique marker
src = remove_voice_block(src, "    # Voice Input\n    c1, c2 = st.columns([1, 4])\n    with c1:\n        audio = mic_recorder(start_prompt=\"🎤 বলুন\", stop_prompt=\"🛑 থামুন\", key='rec_best_market'", "    if audio:", "bestmarket-pre")

# Simpler: now replace ALL remaining mic_recorder calls with a disabled stub so nothing NameErrors
src = src.replace("from streamlit_option_menu import option_menu",
                  "from streamlit_option_menu import option_menu\n\n# Voice recorder disabled: speech deps were unreliable on free hosting.\ndef mic_recorder(*a, **k):\n    return None\n")

open("app.py", "w", encoding="utf-8").write(src)
print("voice blocks handled")
