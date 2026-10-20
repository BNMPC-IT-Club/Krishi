src = open("app.py", encoding="utf-8").read()

def cut(start_marker, end_marker, replacement, label):
    global src
    i = src.find(start_marker)
    j = src.find(end_marker)
    assert i != -1, "start missing: " + label
    assert j != -1 and j > i, "end missing: " + label
    src = src[:i] + replacement + src[j+len(end_marker):]
    print("replaced:", label)

# 1. forecast page voice block -> text search
cut(
"""    # Voice Input
    c1, c2 = st.columns([1, 4])
    with c1:
        audio = mic_recorder(start_prompt=\"🎤 বলুন\", stop_prompt=\"🛑 থামুন\", key='recorder', format=\"wav\", use_container_width=True)

    voice_text = \"\"
""",
"""    # Legacy Geolocation logic removed
""",
"""    # Text search replaces the old mic-recorder (speech deps unreliable in free hosting)
    voice_text = st.text_input(\"🔍 জেলার নাম লিখে খুঁজুন (যেমন: ঢাকা)\", key=\"forecast_search\")
    if voice_text:
        matched = [d for d in district_options_list if d in voice_text or voice_text in d]
        if matched and st.session_state.selected_district_val != matched[0]:
            st.session_state.selected_district_val = matched[0]
            st.rerun()

""", "forecast voice")

# 2. remove duplicate weather integration block on forecast page
i = src.find("    # --- WEATHER INTEGRATION ---\n    weather_icon_url = None")
j = src.find("    # Analysis & Prediction")
assert i != -1 and j != -1 and j > i, "weather dup"
src = src[:i] + src[j:]
print("removed duplicate weather block")

# 3. SMS section -> shareable summary
cut(
"""        # SMS Alert Section (Personalized)
        st.markdown(\"---\")
        st.subheader(\"📲 স্মার্ট এসএমএস অ্যালার্ট\")
""",
"""                    else:
                        st.error(f\"❌ ব্যর্থ: {response}\")
""",
"""        # Shareable alert summary (Twilio SMS removed — paid creds, non-functional)
        st.markdown(\"---\")
        with st.expander(\"📋 শেয়ারযোগ্য সারসংক্ষেপ তৈরি করুন\"):
            insights = get_market_insights(price_df, selected_district, selected_crop)
            msg = f\"স্মার্ট কৃষি বুদ্ধিমত্তা: {selected_district_bn} | {selected_crop_bn} — নমুনা দাম ৳{int(current_price)}/কেজি, পরীক্ষামূলক ৩০ দিনের পূর্বাভাস ৳{int(avg_price)}।\"
            if insights['best_districts_for_crop']:
                top_dist, top_price = insights['best_districts_for_crop'][0]
                d_bn = translate_bn(top_dist, district_translation)
                msg += f\" নমুনা ডেটায় সর্বোচ্চ: {d_bn}তে ৳{int(top_price)}।\"
            st.text_area(\"এই বার্তাটি কপি করে SMS/হোয়াটসঅ্যাপে পাঠাতে পারেন:\", msg, height=90)
            st.caption(\"ℹ️ স্বয়ংক্রিয় এসএমএস (Twilio) পেইড ক্রেডেনশিয়াল প্রয়োজন হওয়ায় সরানো হয়েছে।\")
""", "sms")

open("app.py", "w", encoding="utf-8").write(src)
