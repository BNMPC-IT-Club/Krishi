# -----------------------------------------------------------------------------
# MODULE 6: DASHBOARD (home)
# -----------------------------------------------------------------------------
if menu == "🏠 ড্যাশবোর্ড":
    st.title("🌾 Smart Krishi Buddhimotta")
    st.caption("স্মার্ট কৃষি বুদ্ধিমত্তা — বাংলাদেশের কৃষকদের জন্য ফসলের রোগ শনাক্তকরণ, লাইভ আবহাওয়া, বাজারদর তথ্য ও AI কৃষি সহায়ক।")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🦠 রোগ শনাক্তকরণ", "৩৮ শ্রেণি")
    with c2:
        st.metric("🌦️ আবহাওয়া", "Open-Meteo লাইভ")
    with c3:
        st.metric("💰 বাজারদর", "DAM + নমুনা")
    with c4:
        st.metric("🤖 AI সহায়ক", "Groq (ফ্রি-টিয়ার)")

    st.divider()
    st.markdown(
        "**শুরু করতে যেকোনো একটি খাত বেছে নিন:**\n\n"
        "- 💰 **আজকের বাজারদর** — সরকারি DAM লাইভ রিপোর্ট টানার চেষ্টা করে; না পেলে স্পষ্টভাবে ‘নমুনা ডেটা’ দেখায়।\n"
        "- 📊 **মূল্য পূর্বাভাস** — ঐতিহাসিক vs পূর্বাভাসিত গ্রাফ (পরীক্ষামূলক হিসেবে চিহ্নিত)।\n"
        "- 🦠 **রোগ শনাক্তকরণ** — পাতার ছবি তুলুন/আপলোড করুন, মডেল রোগ, আস্থা ও করণীয় দেখাবে।\n"
        "- 🌦️ **আবহাওয়া** — আপনার জেলার লাইভ আবহাওয়া ও ৭ দিনের পূর্বাভাস (API key লাগে না)।\n"
        "- 🤖 **কৃষি সহায়ক AI** — বাংলায় সাধারণ কৃষি পরামর্শ (Groq key সেট করলে)।\n"
        "- 🌱 **মাটি ও ফসল পরামর্শদাতা** — ডেটাসেট-ভিত্তিক ফসল সুপারিশ।"
    )
    st.info("⚠️ **গুরুত্বপূর্ণ:** অ্যাপের বান্ডেল করা দামের ডেটা নমুনা, লাইভ নয়। সব ফলাফল প্রাথমিক দিকনির্দেশনা — চূড়ান্ত সিদ্ধান্তে উপজেলা কৃষি অফিসের পরামর্শ নিন।")

# -----------------------------------------------------------------------------
# MODULE 7: WEATHER (Open-Meteo, no API key)
# -----------------------------------------------------------------------------
elif menu == "🌦️ আবহাওয়া":
    st.title("🌦️ আবহাওয়া ও কৃষি পরিকল্পনা")
    st.caption("উৎস: Open-Meteo (মডেল-ভিত্তিক পূর্বাভাস) · API key প্রয়োজন নেই")

    dist_names = sorted(DISTRICT_COORDS.keys())
    dist_display = {d: translate_bn(d, district_translation) for d in dist_names}
    sel_bn = st.selectbox("জেলা নির্বাচন করুন", options=[dist_display[d] for d in dist_names],
                          index=dist_names.index('Dhaka'), key="wx_district")
    matched = [k for k, v in dist_display.items() if v == sel_bn]
    sel_en = matched[0] if matched else 'Dhaka'
    lat, lon = DISTRICT_COORDS[sel_en]

    @st.cache_data(ttl=900, show_spinner="আবহাওয়া লোড হচ্ছে...")
    def _wx(_lat, _lon):
        return get_current_weather(_lat, _lon), get_forecast(_lat, _lon, days=7)

    cur_wx, fc = _wx(round(lat, 3), round(lon, 3))

    if cur_wx is None and fc is None:
        st.error("☁️ আবহাওয়া সেবা এখন পাওয়া যাচ্ছে না। ইন্টারনেট সংযোগ পরীক্ষা করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
    else:
        if cur_wx:
            desc, icon = weather_code_info(cur_wx["code"])
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"{icon} তাপমাত্রা", f'{cur_wx["temp"]}°C', help=f'অনুভূত: {cur_wx["feels"]}°C · {desc}')
            m2.metric("💧 আর্দ্রতা", f'{cur_wx["humidity"]}%')
            m3.metric("🌬️ বাতাস", f'{cur_wx["wind"]} km/h')
            m4.metric("🌧️ বৃষ্টি (এখন)", f'{cur_wx["rain_mm"]} mm')
            st.caption(f"সর্বশেষ আপডেট: {cur_wx['time']} (Asia/Dhaka) · অবস্থান: {sel_bn} ({lat}, {lon})")
        if fc:
            st.subheader("📅 আগামী ৭ দিনের পূর্বাভাস")
            fdf = pd.DataFrame(fc)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=fdf["date"], y=fdf["tmax"], name="সর্বোচ্চ °C", mode="lines+markers", line=dict(color="#e76f51")))
            fig.add_trace(go.Scatter(x=fdf["date"], y=fdf["tmin"], name="সর্বনিম্ন °C", mode="lines+markers", line=dict(color="#2a9d8f")))
            fig.add_bar(x=fdf["date"], y=fdf["rain_prob"], name="বৃষ্টির সম্ভাবনা %", marker_color="#264653", opacity=0.35, yaxis="y2")
            fig.update_layout(height=380, margin=dict(t=10, b=10), legend=dict(orientation="h"),
                              yaxis2=dict(title="%", overlaying="y", side="right", range=[0, 100]))
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("🗂️ বিস্তারিত তালিকা"):
                show = fdf.copy()
                show["cond"] = [weather_code_info(c)[0] for c in show["code"]]
                st.dataframe(
                    show[["date", "cond", "tmax", "tmin", "rain_mm", "rain_prob", "wind"]]
                    .rename(columns={"date": "তারিখ", "cond": "আবহাওয়া", "tmax": "সর্বোচ্চ °C",
                                     "tmin": "সর্বনিম্ন °C", "rain_mm": "বৃষ্টি (মিমি)",
                                     "rain_prob": "সম্ভাবনা %", "wind": "বাতাস (km/h)"}),
                    use_container_width=True, hide_index=True)
        st.subheader("🚜 কৃষি পরিকল্পনা পরামর্শ")
        for tip in farm_advice(cur_wx, fc):
            st.markdown(f"- {tip}")
        st.caption("ℹ️ পরামর্শগুলো শুধু উপরের প্রকৃত পূর্বাভাস-চলক থেকে তৈরি; এটি AI-generated নয় এবং নিশ্চিত পূর্বাভাস নয়।")

# -----------------------------------------------------------------------------
# MODULE 8: AI ASSISTANT (Groq)
# -----------------------------------------------------------------------------
elif menu == "🤖 কৃষি সহায়ক AI":
    st.title("🤖 কৃষি সহায়ক AI")
    st.caption("সাধারণ কৃষি পরামর্শ · চালিকাশক্তি: Groq (Llama-3.3-70B) · উত্তর সাধারণ জ্ঞানভিত্তিক, লাইভ ডেটা নয়")

    if not get_groq_key():
        st.warning(
            "⚙️ **AI সহায়ক এখন নিষ্ক্রিয়** — GROQ_API_KEY পাওয়া যায়নি।\n\n"
            "1. [console.groq.com](https://console.groq.com)-এ ফ্রি অ্যাকাউন্ট খুলে API key নিন।\n"
            "2. স্থানীয়ভাবে `.streamlit/secrets.toml`-এ যোগ করুন: `GROQ_API_KEY=\"your_key\"`\n"
            "3. Streamlit Cloud-এ Settings → Secrets-এ একই key বসান।\n\n"
            "কী ছাড়াও অ্যাপের বাকি সব ফিচার স্বাভাবিক চলবে।"
        )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("কৃষি সম্পর্কে প্রশ্ন করুন (বাংলা বা English)...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("চিন্তা করছে..."):
                reply, err = chat_completion(
                    [{"role": m["role"], "content": m["content"]}
                     for m in st.session_state.chat_history[-8:]])
            shown = err if err else reply
            st.markdown(shown)
            st.session_state.chat_history.append({"role": "assistant", "content": shown})
        st.session_state.chat_history = st.session_state.chat_history[-20:]

# -----------------------------------------------------------------------------
# MODULE 9: ABOUT
# -----------------------------------------------------------------------------
elif menu == "ℹ️ প্রকল্প সম্পর্কে":
    st.title("ℹ️ প্রকল্প সম্পর্কে")
    st.markdown("""
### Smart Krishi Buddhimotta (স্মার্ট কৃষি বুদ্ধিমত্তা)
বাংলাদেশের কৃষকদের জন্য একটি উন্মুক্ত, বাংলা-প্রধান কৃষি-বুদ্ধিমত্তা প্ল্যাটফর্ম:
ফসলের রোগ শনাক্তকরণ, লাইভ আবহাওয়া, বাজারদর তথ্য ও AI কৃষি সহায়ক — একটি পরিচ্ছন্ন,
মোবাইল-বান্ধব ইন্টারফেসে।

### কৃতজ্ঞতা ও উৎস (Attribution)
- এটি **Agri-Smart BD** (NawrizTurjo/Agri-Smart-BD, MIT license) প্রকল্পের **অ্যাডাপ্টেড ও উন্নত সংস্করণ**।
- রোগ শনাক্তকরণ: ResNet9, **New Plant Diseases Dataset** (Kaggle: vipoooool/new-plant-diseases-dataset; মূল PlantVillage ডেটা) — মূল notebook-এর সংরক্ষিত ওয়েট পুনর্ব্যবহৃত, পুনঃপ্রশিক্ষণ করা হয়নি।
- আবহাওয়া: [Open-Meteo.com](https://open-meteo.com) (CC-BY 4.0)।
- AI চ্যাট: [Groq](https://groq.com) — Llama-3.3-70B (ফ্রি-টিয়ার)।
- বাজারদর: কৃষি মার্কেট বিভাগ (DAM) market.dam.gov.bd লাইভ রিপোর্ট; বান্ডেল করা CSV **নমুনা ডেটা**।

### সীাবদ্ধতা
- বান্ডেল করা দামের ডেটা বাস্তব পর্যবেক্ষণ নয়; যেসব মূল্য-পূর্বাভাস দেখানো হয় সেগুলো **পরীক্ষামূলক**।
- রোগ মডেল কেবল তার ৩৮টি প্রশিক্ষিত শ্রেণিতে কাজ করে; অন্য ফসলের ছবি ভুল ফলাফল দিতে পারে।
- AI উত্তর সাধারণ জ্ঞানভিত্তিক; রোগ/ওষুধের চূড়ান্ত সিদ্ধান্তে উপজেলা কৃষি অফিসারের পরামর্শ নিন।
""")
    st.caption("🌾 Free & open-source · Streamlit + PyTorch + Open-Meteo + Groq")
