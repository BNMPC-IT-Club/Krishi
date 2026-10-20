src = open("app.py", encoding="utf-8").read()

# 1. Replace the first (forecast-page) "# Voice Input" block header with text search + audio=None
needle = "    # Voice Input\n    c1, c2 = st.columns([1, 4])\n    with c1:\n        audio = mic_recorder(start_prompt=\"\U0001f3a4 \u09ac\u09b2\u09c1\u09a8\", stop_prompt=\"\U0001f6d1 \u09a5\u09be\u09ae\u09c1\u09a8\", key='recorder', format=\"wav\", use_container_width=True)"
i = src.find(needle)
print("needle found at", i)
if i == -1:
    # dump exact bytes around first occurrence for debugging
    k = src.find("# Voice Input")
    print(repr(src[k-10:k+300]))
    raise SystemExit(1)
replacement = ("    # Text search replaces the removed voice recorder (speech deps unreliable on free hosting)\n"
"    voice_text = st.text_input(\"\U0001f50d \u099c\u09c7\u09b2\u09be\u09b0 \u09a8\u09be\u09ae \u09b2\u09bf\u0996\u09c7 \u0996\u09c1\u0981\u099c\u09c1\u09a8 (\u09af\u09c7\u09ae\u09a8: \u09a2\u09be\u0995\u09be)\", key=\"forecast_search\")\n"
"    if voice_text:\n"
"        matched = [d for d in district_options_list if d in voice_text or voice_text in d]\n"
"        if matched and st.session_state.selected_district_val != matched[0]:\n"
"            st.session_state.selected_district_val = matched[0]\n"
"            st.rerun()\n"
"    audio = None\n")
src = src[:i] + replacement + src[i+len(needle):]
open("app.py", "w", encoding="utf-8").write(src)
print("step1 ok")
