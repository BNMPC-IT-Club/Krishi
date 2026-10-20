src = open("app.py", encoding="utf-8").read()

# 1. Insert text-search box before the (stubbed) voice block on forecast page, and neutralize voice processing there
needle = """    # Voice Input
    c1, c2 = st.columns([1, 4])
    with c1:
        audio = mic_recorder(start_prompt="\U0001f3a4 \u09ac\u09b2\u09c1\u09a8", stop_prompt="\U0001f6d1 \u09a5\u09be\u09ae\u09c1\u09a8", key='recorder', format="wav", use_container_width=True)
"""
assert needle in src, "voice needle"
replacement = """    # Text search replaces the removed voice recorder (speech deps unreliable on free hosting)
    voice_text = st.text_input("\U0001f50d \u099c\u09c7\u09b2\u09be\u09b0 \u09a8\u09be\u09ae \u09b2\u09bf\u0996\u09c7 \u0996\u09c1\u0981\u099c\u09c1\u09a8 (\u09af\u09c7\u09ae\u09a8: \u09a2\u09be\u0995\u09be)", key="forecast_search")
    if voice_text:
        matched = [d for d in district_options_list if d in voice_text or voice_text in d]
        if matched and st.session_state.selected_district_val != matched[0]:
            st.session_state.selected_district_val = matched[0]
            st.rerun()
    audio = None
"""
src = src.replace(needle, replacement, 1)
print("1 ok")

# 2. Remove duplicate weather integration block (from marker to Analysis & Prediction)
i = src.find("    # --- WEATHER INTEGRATION ---\n    weather_icon_url = None")
j = src.find("    # Analysis & Prediction")
assert i != -1 and j != -1 and j > i, "weather dup"
src = src[:i] + src[j:]
print("2 ok")

# 3. SMS section -> shareable summary. Find start and end by unique anchors.
s = src.find("        # SMS Alert Section (Personalized)")
e = src.find("# -----------------------------------------------------------------------------\n# MODULE 2: BEST MARKET FINDER")
assert s != -1 and e != -1 and e > s, "sms anchors"
new_sms = '''        # Shareable alert summary (Twilio SMS removed: paid creds, non-functional)
        st.markdown("---")
        with st.expander("\U0001f4cb \u09b6\u09c7\u09df\u09be\u09b0\u09af\u09cb\u0997\u09cd\u09af \u09b8\u09be\u09b0\u09b8\u0982\u0995\u09cd\u09b7\u09c7\u09aa"):
            insights = get_market_insights(price_df, selected_district, selected_crop)
            msg = f"\u09b8\u09cd\u09ae\u09be\u09b0\u09cd\u099f \u0995\u09c3\u09b7\u09bf \u09ac\u09c1\u09a6\u09cd\u09a7\u09bf\u09ae\u09ce\u09a4\u09be: {selected_district_bn} | {selected_crop_bn} \u2014 \u09a8\u09ae\u09c1\u09a8\u09be \u09a6\u09be\u09ae \u09f3{int(current_price)}/\u0995\u09c7\u099c\u09bf, \u09aa\u09b0\u09c0\u0995\u09cd\u09b7\u09be\u09ae\u09c2\u09b2\u0995 \u09aa\u09c2\u09b0\u09cd\u09ac\u09be\u09ad\u09be\u09b8 \u09f3{int(avg_price)}\u0964"
            if insights['best_districts_for_crop']:
                top_dist, top_price = insights['best_districts_for_crop'][0]
                d_bn = translate_bn(top_dist, district_translation)
                msg += f" \u09a8\u09ae\u09c1\u09a8\u09be \u09a1\u09c7\u099f\u09be\u09df \u09b8\u09b0\u09cd\u09ac\u09cb\u099a\u09cd\u099a: {d_bn}\u09a4\u09c7 \u09f3{int(top_price)}\u0964"
            st.text_area("\u098f\u0987 \u09ac\u09be\u09b0\u09cd\u09a4\u09be\u099f\u09bf \u0995\u09aa\u09bf \u0995\u09b0\u09c7 SMS/\u09b9\u09cb\u09df\u09be\u099f\u09b8\u09cd\u09af\u09be\u09aa\u09c7 \u09aa\u09be\u09a0\u09be\u09a8:", msg, height=90)
            st.caption("\u2139\ufe0f \u09b8\u09cd\u09ac\u09df\u0982\u0995\u09cd\u09b0\u09bf\u09df \u098f\u09b8\u098f\u09ae\u09b8 (Twilio) \u09aa\u09c7\u0987\u09a1 \u0995\u09cd\u09b0\u09c7\u09a1\u09c7\u09a8\u09b6\u09bf\u09df\u09be\u09b2 \u09b9\u0993\u09df\u09be\u09df \u09b8\u09b0\u09be\u09a8\u09cb \u09b9\u09df\u09c7\u099b\u09c7\u0964")

'''
src = src[:s] + new_sms + src[e:]
print("3 ok")

open("app.py", "w", encoding="utf-8").write(src)
