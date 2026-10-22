"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Bot, Bug, CalendarDays, ChevronRight, CloudDrizzle, CloudRain, CloudSun, Crosshair,
  Droplets, FileWarning, Gauge, Leaf, LoaderCircle, Map, MapPin, Menu, MessageCircle,
  MoveUpRight, Navigation, ScanLine, Send, ShieldCheck, ShoppingBasket, Sparkles,
  Sprout, ThermometerSun, TrendingDown, TrendingUp, Upload, Wind, X,
} from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  cropGuides, createForecast, createPriceHistory, crops, districts, formatBnNumber, nearestDistrict,
} from "@/lib/agri-data";

type Screen = "dashboard" | "market" | "forecast" | "weather" | "disease" | "chat" | "advice";
type Coordinates = { lat: number; lng: number; source: "district" | "device" };
type WeatherData = {
  weather: {
    current: { temperature_2m: number; relative_humidity_2m: number; apparent_temperature: number; precipitation: number; weather_code: number; wind_speed_10m: number };
    daily: { time: string[]; weather_code: number[]; temperature_2m_max: number[]; temperature_2m_min: number[]; precipitation_probability_max: number[]; precipitation_sum: number[]; wind_speed_10m_max: number[] };
  };
  source: string;
  fetchedAt: string;
};
type ChatMessage = { role: "user" | "assistant"; content: string };

const navigation: Array<{ id: Screen; label: string; icon: typeof Sprout }> = [
  { id: "dashboard", label: "ড্যাশবোর্ড", icon: Sprout },
  { id: "market", label: "আজকের বাজারদর", icon: ShoppingBasket },
  { id: "forecast", label: "মূল্য পূর্বাভাস", icon: TrendingUp },
  { id: "weather", label: "আবহাওয়া", icon: CloudSun },
  { id: "disease", label: "রোগ সহায়তা", icon: ScanLine },
  { id: "chat", label: "AI কৃষি সহায়ক", icon: MessageCircle },
  { id: "advice", label: "ফসল পরামর্শ", icon: Leaf },
];

const wmo = (code: number) => {
  if ([0, 1].includes(code)) return { label: "পরিষ্কার আকাশ", icon: CloudSun, color: "sun" };
  if ([2, 3, 45, 48].includes(code)) return { label: "আংশিক মেঘলা", icon: CloudSun, color: "cloud" };
  if ([51, 53, 55, 56, 57].includes(code)) return { label: "গুঁড়ি গুঁড়ি বৃষ্টি", icon: CloudDrizzle, color: "rain" };
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return { label: "বৃষ্টি", icon: CloudRain, color: "rain" };
  if ([95, 96, 99].includes(code)) return { label: "বজ্রসহ বৃষ্টি", icon: CloudRain, color: "storm" };
  return { label: "পরিবর্তনশীল", icon: CloudSun, color: "cloud" };
};

const banglaDate = (value: string, weekday = false) => new Intl.DateTimeFormat("bn-BD", {
  weekday: weekday ? "short" : undefined, day: "numeric", month: "short",
}).format(new Date(`${value}T12:00:00`));

const mapUrl = (lat: number, lng: number) => {
  const offset = 0.11;
  const bbox = `${lng - offset}%2C${lat - offset}%2C${lng + offset}%2C${lat + offset}`;
  return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lng}`;
};

export default function HomePage() {
  const [active, setActive] = useState<Screen>("dashboard");
  const [districtName, setDistrictName] = useState("ঢাকা");
  const [crop, setCrop] = useState("ধান");
  const initialDistrict = districts.find((item) => item.name === "ঢাকা") ?? districts[0];
  const [coordinates, setCoordinates] = useState<Coordinates>({ lat: initialDistrict.lat, lng: initialDistrict.lng, source: "district" });
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [weatherError, setWeatherError] = useState("");
  const [weatherLoading, setWeatherLoading] = useState(true);
  const [locating, setLocating] = useState(false);
  const [locationMessage, setLocationMessage] = useState("জেলা নির্বাচন করে বা নিজের অবস্থান থেকে পূর্বাভাস দেখুন");
  const [mobileNav, setMobileNav] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "আসসালামু আলাইকুম। আমি ক্ষেতসাথী। ফসল, আবহাওয়া বা পরিচর্যা নিয়ে প্রশ্ন করতে পারেন।" },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [plantImage, setPlantImage] = useState<string | null>(null);
  const [plantFileName, setPlantFileName] = useState("");
  const [symptom, setSymptom] = useState("");
  const [diseaseAdvice, setDiseaseAdvice] = useState("");
  const [diseaseLoading, setDiseaseLoading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const selectedDistrict = districts.find((item) => item.name === districtName) ?? districts[0];
  const history = useMemo(() => createPriceHistory(crop, districtName), [crop, districtName]);
  const forecast = useMemo(() => createForecast(crop, districtName), [crop, districtName]);
  const latestPrice = history.at(-1)?.price ?? 0;
  const priceChange = latestPrice - (history.at(-2)?.price ?? latestPrice);
  const chartData = useMemo(() => [
    ...history.map((item) => ({ ...item, observed: item.price })),
    ...forecast.map((item) => ({ ...item, projected: item.price })),
  ], [history, forecast]);
  const guide = cropGuides[crop] ?? cropGuides["ধান"];

  useEffect(() => {
    const controller = new AbortController();
    async function getWeather() {
      setWeatherLoading(true);
      setWeatherError("");
      try {
        const response = await fetch(`/api/weather?lat=${coordinates.lat.toFixed(4)}&lng=${coordinates.lng.toFixed(4)}`, { signal: controller.signal });
        const data = await response.json() as WeatherData & { error?: string };
        if (!response.ok) throw new Error(data.error ?? "আবহাওয়ার তথ্য পাওয়া যায়নি।");
        setWeather(data);
      } catch (error) {
        if ((error as Error).name !== "AbortError") setWeatherError(error instanceof Error ? error.message : "আবহাওয়ার তথ্য পাওয়া যায়নি।");
      } finally {
        if (!controller.signal.aborted) setWeatherLoading(false);
      }
    }
    void getWeather();
    return () => controller.abort();
  }, [coordinates]);

  function selectDistrict(name: string) {
    const district = districts.find((item) => item.name === name) ?? districts[0];
    setDistrictName(district.name);
    setCoordinates({ lat: district.lat, lng: district.lng, source: "district" });
    setLocationMessage(`${district.name} জেলার অবস্থান অনুযায়ী পূর্বাভাস দেখা হচ্ছে`);
  }

  function detectLocation() {
    if (!navigator.geolocation) {
      setLocationMessage("এই ব্রাউজারে অবস্থান সেবা নেই। তালিকা থেকে জেলা বেছে নিন।");
      return;
    }
    setLocating(true);
    setLocationMessage("আপনার ডিভাইস থেকে অবস্থান নেওয়া হচ্ছে…");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const nearby = nearestDistrict(coords.latitude, coords.longitude);
        setCoordinates({ lat: coords.latitude, lng: coords.longitude, source: "device" });
        setDistrictName(nearby.name);
        setLocationMessage(`আপনার অবস্থানের নিকটতম জেলা: ${nearby.name}। মানচিত্রে সঠিক অবস্থান দেখানো হয়েছে।`);
        setLocating(false);
      },
      () => {
        setLocationMessage("অবস্থান অনুমতি পাওয়া যায়নি। ব্রাউজার সেটিংস থেকে অনুমতি দিন বা জেলা বেছে নিন।");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 300000 },
    );
  }

  async function requestAssistant(messages: ChatMessage[], context: string) {
    const response = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ messages, context }),
    });
    const data = await response.json() as { answer?: string; error?: string };
    if (!response.ok || !data.answer) throw new Error(data.error ?? "AI সেবাটি সাড়া দিচ্ছে না।");
    return data.answer;
  }

  async function sendChat(event?: FormEvent) {
    event?.preventDefault();
    const question = chatInput.trim();
    if (!question || chatLoading) return;
    const next = [...chatMessages, { role: "user" as const, content: question }];
    setChatMessages(next);
    setChatInput("");
    setChatLoading(true);
    setChatError("");
    try {
      const answer = await requestAssistant(next, `নির্বাচিত জেলা: ${districtName}; ফসল: ${crop}. বাজারদরের অংশটি নমুনা/প্রোটোটাইপ ডেটা, লাইভ দাম নয়।`);
      setChatMessages((current) => [...current, { role: "assistant", content: answer }]);
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "AI সেবাটি সাড়া দিচ্ছে না।");
    } finally {
      setChatLoading(false);
    }
  }

  function onPlantImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/") || file.size > 8 * 1024 * 1024) {
      setDiseaseAdvice("অনুগ্রহ করে ৮ এমবি-র মধ্যে একটি পরিষ্কার JPG, PNG বা WebP ছবি দিন।");
      return;
    }
    if (plantImage) URL.revokeObjectURL(plantImage);
    setPlantImage(URL.createObjectURL(file));
    setPlantFileName(file.name);
    setDiseaseAdvice("");
  }

  async function getDiseaseAdvice() {
    if (!plantImage) {
      setDiseaseAdvice("আগে আক্রান্ত পাতার একটি পরিষ্কার ছবি যোগ করুন।");
      return;
    }
    setDiseaseLoading(true);
    setDiseaseAdvice("");
    try {
      const question = `আমি ${crop} ফসলের পাতার একটি ছবি তুলেছি। চোখে দেখা লক্ষণ: ${symptom || "লক্ষণ লেখা হয়নি"}। ছবি ছাড়া নিশ্চিত রোগ নির্ণয় না করে, মাঠে যাচাইয়ের জন্য নিরাপদ ও বাস্তবসম্মত পরবর্তী পদক্ষেপ বলুন।`;
      const answer = await requestAssistant([{ role: "user", content: question }], "এটি ছবি-সমর্থিত নিশ্চিত রোগ নির্ণয় নয়। ব্যবহারকারী কেবল ফাইলের স্থানীয় প্রিভিউ দিয়েছেন; AI-কে ছবির বিষয়বস্তু দেখা হয়েছে বলে দাবি করতে নিষেধ করা হলো।");
      setDiseaseAdvice(answer);
    } catch (error) {
      setDiseaseAdvice(error instanceof Error ? error.message : "এখন পরামর্শ আনা যাচ্ছে না।");
    } finally {
      setDiseaseLoading(false);
    }
  }

  const currentWeather = weather?.weather.current;
  const currentWeatherInfo = wmo(currentWeather?.weather_code ?? 2);
  const WeatherIcon = currentWeatherInfo.icon;

  return (
    <main className="app-shell">
      <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <div className="brand-lockup">
          <div className="brand-mark"><Sprout size={25} strokeWidth={2.4} /></div>
          <div><strong>ক্ষেতসাথী</strong><span>কৃষি বুদ্ধিমত্তা</span></div>
          <button className="icon-button close-menu" onClick={() => setMobileNav(false)} aria-label="মেনু বন্ধ করুন"><X size={19} /></button>
        </div>
        <div className="sidebar-label">মূল নেভিগেশন</div>
        <nav className="nav-list" aria-label="প্রধান মেনু">
          {navigation.map((item) => {
            const Icon = item.icon;
            return <button key={item.id} onClick={() => { setActive(item.id); setMobileNav(false); }} className={`nav-item ${active === item.id ? "active" : ""}`}>
              <Icon size={19} strokeWidth={active === item.id ? 2.5 : 2} /><span>{item.label}</span>{active === item.id && <ChevronRight size={16} className="nav-arrow" />}
            </button>;
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="side-status"><span className="status-dot" /> সবার জন্য সহজ কৃষি সহায়তা</div>
          <p>আবহাওয়া: Open-Meteo<br />মানচিত্র: OpenStreetMap</p>
        </div>
      </aside>
      {mobileNav && <button aria-label="মেনু বন্ধ করুন" className="mobile-backdrop" onClick={() => setMobileNav(false)} />}

      <section className="content-area">
        <header className="topbar">
          <button className="icon-button hamburger" onClick={() => setMobileNav(true)} aria-label="মেনু খুলুন"><Menu size={22} /></button>
          <div className="breadcrumb"><span>ক্ষেতসাথী</span><ChevronRight size={14} /><strong>{navigation.find((item) => item.id === active)?.label}</strong></div>
          <div className="topbar-actions"><div className="live-label"><span className="status-dot" /> সেবা চালু</div><button className="profile-button" onClick={() => setActive("chat")}><Bot size={17} /><span>AI সহায়ক</span></button></div>
        </header>

        <div className="page-content">
          {active === "dashboard" && <Dashboard
            districtName={districtName} crop={crop} setActive={setActive} selectDistrict={selectDistrict}
            weather={weather} weatherLoading={weatherLoading} weatherError={weatherError} currentInfo={currentWeatherInfo}
            latestPrice={latestPrice} priceChange={priceChange} history={history}
          />}
          {active === "market" && <MarketPrice districtName={districtName} crop={crop} selectDistrict={selectDistrict} setCrop={setCrop} history={history} />}
          {active === "forecast" && <Forecast districtName={districtName} crop={crop} selectDistrict={selectDistrict} setCrop={setCrop} latestPrice={latestPrice} forecast={forecast} chartData={chartData} />}
          {active === "weather" && <Weather
            districtName={districtName} coordinates={coordinates} weather={weather} loading={weatherLoading} error={weatherError}
            selectDistrict={selectDistrict} detectLocation={detectLocation} locating={locating} locationMessage={locationMessage}
          />}
          {active === "disease" && <DiseaseAssistant crop={crop} setCrop={setCrop} plantImage={plantImage} plantFileName={plantFileName} fileInput={fileInput} onImage={onPlantImage} symptom={symptom} setSymptom={setSymptom} advice={diseaseAdvice} loading={diseaseLoading} getAdvice={getDiseaseAdvice} />}
          {active === "chat" && <Chat
            messages={chatMessages} input={chatInput} setInput={setChatInput} onSubmit={sendChat} loading={chatLoading} error={chatError}
            districtName={districtName} setCrop={setCrop} setActive={setActive}
          />}
          {active === "advice" && <CropAdvice crop={crop} districtName={districtName} setCrop={setCrop} selectDistrict={selectDistrict} guide={guide} />}
        </div>
      </section>
    </main>
  );
}

function ScreenTitle({ eyebrow, title, children }: { eyebrow: string; title: string; children?: React.ReactNode }) {
  return <div className="screen-title"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1></div>{children}</div>;
}

function DistrictSelect({ value, onChange, label = "জেলা নির্বাচন" }: { value: string; onChange: (value: string) => void; label?: string }) {
  const grouped = districts.reduce<Record<string, typeof districts>>((groups, district) => { (groups[district.division] ??= []).push(district); return groups; }, {});
  return <label className="field-control"><span>{label}</span><div className="select-wrap"><MapPin size={17} /><select value={value} onChange={(event) => onChange(event.target.value)}>{Object.entries(grouped).map(([division, entries]) => <optgroup label={`${division} বিভাগ`} key={division}>{entries.map((entry) => <option value={entry.name} key={entry.name}>{entry.name}</option>)}</optgroup>)}</select></div></label>;
}

function CropSelect({ value, onChange, label = "ফসল নির্বাচন" }: { value: string; onChange: (value: string) => void; label?: string }) {
  return <label className="field-control"><span>{label}</span><div className="select-wrap"><Leaf size={17} /><select value={value} onChange={(event) => onChange(event.target.value)}>{crops.map((entry) => <option value={entry} key={entry}>{entry}</option>)}</select></div></label>;
}

function Dashboard({ districtName, crop, setActive, selectDistrict, weather, weatherLoading, weatherError, currentInfo, latestPrice, priceChange, history }: {
  districtName: string; crop: string; setActive: (screen: Screen) => void; selectDistrict: (value: string) => void; weather: WeatherData | null; weatherLoading: boolean; weatherError: string; currentInfo: ReturnType<typeof wmo>; latestPrice: number; priceChange: number; history: Array<{ day: string; price: number }>;
}) {
  const CurrentIcon = currentInfo.icon;
  return <>
    <ScreenTitle eyebrow="বাংলাদেশের কৃষকের জন্য ডিজিটাল সহায়তা" title="আপনার ক্ষেত, আপনার সিদ্ধান্ত"><DistrictSelect value={districtName} onChange={selectDistrict} /></ScreenTitle>
    <section className="hero-panel">
      <div className="hero-copy"><div className="hero-kicker"><Sparkles size={16} /> কৃষি পরিকল্পনার স্মার্ট শুরু</div><h2>আজকের তথ্য দিয়ে<br /><em>আগামীর ফসল</em> গুছিয়ে নিন।</h2><p>আবহাওয়া, বাজারের নমুনা প্রবণতা ও ফসল পরিচর্যার প্রয়োজনীয় তথ্য একই জায়গায়—সহজ বাংলায়।</p><div className="hero-actions"><button className="primary-button" onClick={() => setActive("weather")}>আবহাওয়া দেখুন <ChevronRight size={17} /></button><button className="text-button" onClick={() => setActive("chat")}>AI-কে প্রশ্ন করুন</button></div></div>
      <div className="hero-orb"><div className="hero-leaf leaf-one" /><div className="hero-leaf leaf-two" /><div className="hero-sun" /><div className="hero-field"><span /><span /><span /></div><div className="hero-location"><MapPin size={17} /><div><small>নির্বাচিত এলাকা</small><strong>{districtName}</strong></div></div></div>
    </section>
    <section className="metrics-grid">
      <article className="metric-card weather-metric"><div className="metric-icon sun"><CurrentIcon size={22} /></div><div><p>বর্তমান আবহাওয়া</p>{weatherLoading ? <span className="loading-line">আপডেট হচ্ছে</span> : weatherError ? <strong className="metric-error">তথ্য অনুপলব্ধ</strong> : <><strong>{formatBnNumber(weather?.weather.current.temperature_2m ?? 0, 1)}°</strong><span>{currentInfo.label} · {districtName}</span></>}</div><button onClick={() => setActive("weather")} aria-label="আবহাওয়া বিস্তারিত"><ChevronRight size={18} /></button></article>
      <article className="metric-card"><div className="metric-icon green"><ShoppingBasket size={21} /></div><div><p>{crop} এর নমুনা মূল্য</p><strong>৳ {formatBnNumber(latestPrice, 1)}</strong><span className={priceChange >= 0 ? "positive" : "negative"}>{priceChange >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />} গত দিনের তুলনায় {formatBnNumber(Math.abs(priceChange), 1)} টাকা</span></div><button onClick={() => setActive("market")} aria-label="বাজারদর বিস্তারিত"><ChevronRight size={18} /></button></article>
      <article className="metric-card"><div className="metric-icon blue"><Sprout size={21} /></div><div><p>ফসল পরিচর্যা</p><strong>আজকের করণীয়</strong><span>আবহাওয়া দেখে সেচ পরিকল্পনা করুন</span></div><button onClick={() => setActive("advice")} aria-label="ফসল পরামর্শ বিস্তারিত"><ChevronRight size={18} /></button></article>
    </section>
    <section className="dashboard-grid">
      <article className="panel trend-panel"><div className="panel-heading"><div><p className="section-kicker">নমুনা বাজার পর্যবেক্ষণ</p><h2>{crop} এর মূল্য প্রবণতা</h2></div><button className="quiet-link" onClick={() => setActive("forecast")}>পূর্বাভাস <MoveUpRight size={15} /></button></div><div className="mini-chart"><ResponsiveContainer width="100%" height={220}><AreaChart data={history}><defs><linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#218a63" stopOpacity={0.27}/><stop offset="100%" stopColor="#218a63" stopOpacity={0}/></linearGradient></defs><XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fill: "#728177", fontSize: 11 }} interval={2}/><YAxis hide domain={["dataMin - 4", "dataMax + 4"]}/><Tooltip formatter={(value) => [`৳ ${formatBnNumber(Number(value), 1)}`, "নমুনা মূল্য"]} labelStyle={{ color: "#17362a" }} contentStyle={{ borderRadius: 12, border: "1px solid #e1e9e4" }}/><Area type="monotone" dataKey="price" stroke="#218a63" strokeWidth={2.5} fill="url(#priceGradient)" /></AreaChart></ResponsiveContainer></div><p className="chart-caption"><FileWarning size={14} /> প্রদর্শিত মূল্য প্রোটোটাইপ ডেটা; এটি লাইভ বাজারদর নয়।</p></article>
      <article className="panel shortcuts-panel"><div className="panel-heading"><div><p className="section-kicker">দ্রুত কাজ</p><h2>যা করতে চান</h2></div></div><div className="shortcut-grid"><button onClick={() => setActive("market")}><ShoppingBasket size={20}/><span>বাজারদর</span><ChevronRight size={15}/></button><button onClick={() => setActive("forecast")}><TrendingUp size={20}/><span>মূল্য পূর্বাভাস</span><ChevronRight size={15}/></button><button onClick={() => setActive("disease")}><ScanLine size={20}/><span>রোগ সহায়তা</span><ChevronRight size={15}/></button><button onClick={() => setActive("chat")}><MessageCircle size={20}/><span>AI সহায়ক</span><ChevronRight size={15}/></button></div></article>
    </section>
  </>;
}

function MarketPrice({ districtName, crop, selectDistrict, setCrop, history }: { districtName: string; crop: string; selectDistrict: (value: string) => void; setCrop: (value: string) => void; history: Array<{ day: string; price: number }> }) {
  const displayed = [crop, "আলু", "পেঁয়াজ", "টমেটো", "বেগুন"].filter((value, index, all) => all.indexOf(value) === index);
  return <>
    <ScreenTitle eyebrow="প্রোটোটাইপ বাজার তথ্য" title="আজকের বাজারদর"><div className="screen-filters"><DistrictSelect value={districtName} onChange={selectDistrict} /><CropSelect value={crop} onChange={setCrop} /></div></ScreenTitle>
    <div className="notice info-notice"><FileWarning size={19}/><div><strong>স্বচ্ছতা নোট</strong><p>এখানের দামগুলো ডেমো/প্রোটোটাইপ ডেটা, লাইভ বা সরকারি বাজারদর নয়। কেনাবেচার আগে স্থানীয় বাজার ও নির্ভরযোগ্য উৎসে যাচাই করুন।</p></div></div>
    <section className="market-overview"><div><p className="section-kicker">নির্বাচিত বাজার এলাকা</p><h2>{districtName} জেলা</h2><span>প্রতি কেজি · নমুনা তথ্য · ২১ মার্চ ২০২৬</span></div><div className="market-stat"><span>নির্বাচিত পণ্য</span><strong>{crop}</strong></div><div className="market-stat"><span>সর্বশেষ নমুনা মূল্য</span><strong>৳ {formatBnNumber(history.at(-1)?.price ?? 0, 1)}</strong></div></section>
    <section className="market-table panel"><div className="table-head"><div><h2>প্রয়োজনীয় পণ্যের তালিকা</h2><p>একই পণ্যের পুনরাবৃত্তি ছাড়া একটি সংক্ষিপ্ত তুলনা</p></div><span className="data-badge">নমুনা ডেটা</span></div><div className="table-scroll"><table><thead><tr><th>পণ্য</th><th>নমুনা মূল্য</th><th>একক</th><th>প্রবণতা</th><th>তথ্যের ধরন</th></tr></thead><tbody>{displayed.map((item, index) => { const price = createPriceHistory(item, districtName).at(-1)?.price ?? 0; const delta = price - (createPriceHistory(item, districtName).at(-2)?.price ?? price); return <tr key={item}><td><span className="commodity-icon"><Leaf size={15}/></span>{item}</td><td className="price-cell">৳ {formatBnNumber(price, 1)}</td><td>প্রতি কেজি</td><td><span className={delta >= 0 ? "trend-up" : "trend-down"}>{delta >= 0 ? <TrendingUp size={14}/> : <TrendingDown size={14}/>} {formatBnNumber(Math.abs(delta), 1)}</span></td><td><span className="sample-tag">প্রোটোটাইপ</span></td></tr>; })}</tbody></table></div></section>
    <div className="source-strip"><ShieldCheck size={19}/><div><strong>লাইভ ডেটা সংযোগের পরিকল্পনা</strong><span>সরকারি/বিশ্বস্ত উৎস নির্ভরযোগ্যভাবে পাওয়া গেলে উৎস, রিপোর্টের তারিখ এবং হালনাগাদের সময় আলাদাভাবে দেখানো হবে।</span></div></div>
  </>;
}

function Forecast({ districtName, crop, selectDistrict, setCrop, latestPrice, forecast, chartData }: { districtName: string; crop: string; selectDistrict: (value: string) => void; setCrop: (value: string) => void; latestPrice: number; forecast: Array<{ day: string; price: number }>; chartData: Array<{ day: string; observed?: number; projected?: number }> }) {
  const predictedAverage = forecast.reduce((sum, item) => sum + item.price, 0) / forecast.length;
  const delta = predictedAverage - latestPrice;
  return <>
    <ScreenTitle eyebrow="পরীক্ষামূলক মূল্য বিশ্লেষণ" title="মূল্য পূর্বাভাস"><div className="screen-filters"><DistrictSelect value={districtName} onChange={selectDistrict}/><CropSelect value={crop} onChange={setCrop}/></div></ScreenTitle>
    <div className="notice warning-notice"><Gauge size={19}/><div><strong>পূর্বাভাস, প্রতিশ্রুতি নয়</strong><p>এই অংশ প্রোটোটাইপ বাজার ধারার ওপর তৈরি পরীক্ষামূলক হিসাব। বাস্তব বিক্রয়, মজুদ বা চাষের সিদ্ধান্ত নেওয়ার আগে স্থানীয় বাজার ও কৃষি কর্মকর্তার তথ্য যাচাই করুন।</p></div></div>
    <section className="forecast-stats"><article><span>সাম্প্রতিক নমুনা মূল্য</span><strong>৳ {formatBnNumber(latestPrice, 1)}</strong><small>প্রতি কেজি</small></article><article><span>১৪ দিনের গড় পূর্বাভাস</span><strong>৳ {formatBnNumber(predictedAverage, 1)}</strong><small>প্রতি কেজি</small></article><article><span>সম্ভাব্য পরিবর্তন</span><strong className={delta >= 0 ? "positive-text" : "negative-text"}>{delta >= 0 ? "+" : ""}{formatBnNumber(delta, 1)} টাকা</strong><small>সাম্প্রতিক নমুনা দামের তুলনায়</small></article></section>
    <section className="panel forecast-chart"><div className="panel-heading"><div><p className="section-kicker">{districtName} · {crop}</p><h2>পর্যবেক্ষণ ও পূর্বাভাস</h2></div><div className="legend"><span><i className="observed-dot"/>পর্যবেক্ষিত নমুনা</span><span><i className="forecast-dot"/>পরীক্ষামূলক পূর্বাভাস</span></div></div><ResponsiveContainer width="100%" height={330}><LineChart data={chartData} margin={{ top: 10, right: 6, left: -20, bottom: 0 }}><CartesianGrid stroke="#edf1ed" vertical={false}/><XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fill: "#728177", fontSize: 11 }} interval={2}/><YAxis tickLine={false} axisLine={false} tick={{ fill: "#728177", fontSize: 11 }}/><Tooltip formatter={(value) => [`৳ ${formatBnNumber(Number(value), 1)}`, ""]} contentStyle={{ borderRadius: 12, border: "1px solid #e1e9e4" }}/><Line type="monotone" dataKey="observed" name="পর্যবেক্ষণ" stroke="#218a63" strokeWidth={3} dot={false} activeDot={{ r: 5 }}/><Line type="monotone" dataKey="projected" name="পূর্বাভাস" stroke="#d68b2a" strokeWidth={3} strokeDasharray="7 5" dot={false} activeDot={{ r: 5 }}/></LineChart></ResponsiveContainer></section>
    <section className="forecast-days">{forecast.slice(0, 7).map((item, index) => <div key={item.day} className={index === 0 ? "today" : ""}><span>{index === 0 ? "আগামীকাল" : item.day}</span><strong>৳ {formatBnNumber(item.price, 1)}</strong><small>প্রতি কেজি</small></div>)}</section>
  </>;
}

function Weather({ districtName, coordinates, weather, loading, error, selectDistrict, detectLocation, locating, locationMessage }: { districtName: string; coordinates: Coordinates; weather: WeatherData | null; loading: boolean; error: string; selectDistrict: (value: string) => void; detectLocation: () => void; locating: boolean; locationMessage: string }) {
  const current = weather?.weather.current;
  const weatherInfo = wmo(current?.weather_code ?? 2);
  const MainWeatherIcon = weatherInfo.icon;
  const rainfallDays = weather?.weather.daily.precipitation_probability_max.filter((value) => value >= 50).length ?? 0;
  return <>
    <ScreenTitle eyebrow="Open-Meteo থেকে পূর্বাভাস" title="আবহাওয়া ও অবস্থান"><DistrictSelect value={districtName} onChange={selectDistrict}/></ScreenTitle>
    <section className="location-panel panel"><div><p className="section-kicker">সঠিক জায়গা, প্রাসঙ্গিক পূর্বাভাস</p><h2>আপনি কোথায় আছেন?</h2><p>{locationMessage}</p><button className="primary-button" onClick={detectLocation} disabled={locating}>{locating ? <LoaderCircle className="spin" size={17}/> : <Crosshair size={17}/>} {locating ? "অবস্থান নেওয়া হচ্ছে" : "আমার অবস্থান ব্যবহার করুন"}</button><small><MapPin size={13}/> অনুমতি দিলে আপনার ডিভাইসের অবস্থান ব্যবহার করা হবে; কোনো API key প্রয়োজন নেই।</small></div><div className="map-frame"><iframe title="OpenStreetMap অবস্থান" src={mapUrl(coordinates.lat, coordinates.lng)} loading="lazy"/><a href={`https://www.openstreetmap.org/?mlat=${coordinates.lat}&mlon=${coordinates.lng}#map=10/${coordinates.lat}/${coordinates.lng}`} target="_blank" rel="noreferrer"><Map size={15}/> OpenStreetMap-এ বড় করে দেখুন</a></div></section>
    {loading ? <div className="weather-loading panel"><LoaderCircle className="spin" size={21}/> সর্বশেষ আবহাওয়ার তথ্য আনা হচ্ছে…</div> : error ? <div className="notice warning-notice"><FileWarning size={19}/><div><strong>আবহাওয়া সাময়িকভাবে অনুপলব্ধ</strong><p>{error}</p></div></div> : current && weather ? <>
      <section className="weather-now"><article className="weather-main"><div className={`weather-symbol ${weatherInfo.color}`}><MainWeatherIcon size={49}/></div><div><p>{districtName} · {coordinates.source === "device" ? "আপনার অবস্থান" : "জেলা কেন্দ্র"}</p><strong>{formatBnNumber(current.temperature_2m, 1)}°</strong><span>অনুভূত হচ্ছে {formatBnNumber(current.apparent_temperature, 1)}° · {weatherInfo.label}</span></div></article><article><ThermometerSun size={21}/><span>আর্দ্রতা</span><strong>{formatBnNumber(current.relative_humidity_2m)}%</strong></article><article><Wind size={21}/><span>বাতাসের গতি</span><strong>{formatBnNumber(current.wind_speed_10m, 1)} কিমি/ঘ.</strong></article><article><Droplets size={21}/><span>বৃষ্টিপাত</span><strong>{formatBnNumber(current.precipitation, 1)} মিমি</strong></article></section>
      <section className="weather-forecast panel"><div className="panel-heading"><div><p className="section-kicker">সাত দিনের পরিকল্পনা</p><h2>সহজ পূর্বাভাস</h2></div><span className="source-label">উৎস: {weather.source}</span></div><div className="forecast-grid">{weather.weather.daily.time.map((date, index) => { const info = wmo(weather.weather.daily.weather_code[index]); const Icon = info.icon; return <article key={date} className={index === 0 ? "forecast-today" : ""}><p>{index === 0 ? "আজ" : banglaDate(date, true)}</p><Icon className={`weather-small ${info.color}`} size={25}/><strong>{formatBnNumber(weather.weather.daily.temperature_2m_max[index])}° <small>{formatBnNumber(weather.weather.daily.temperature_2m_min[index])}°</small></strong><span><Droplets size={13}/>{formatBnNumber(weather.weather.daily.precipitation_probability_max[index])}%</span><em>{info.label}</em></article>; })}</div></section>
      <section className="weather-advisory"><div className="advisory-icon"><Sprout size={22}/></div><div><p className="section-kicker">খেতের জন্য সতর্ক বার্তা</p><h2>{rainfallDays > 0 ? `আগামী ৭ দিনে ${formatBnNumber(rainfallDays)} দিন বৃষ্টির সম্ভাবনা আছে` : "আগামী ৭ দিনে বড় বৃষ্টির সম্ভাবনা কম"}</h2><p>{rainfallDays > 0 ? "নালা ও পানি নিষ্কাশনের পথ পরিষ্কার রাখুন। স্প্রে বা সার প্রয়োগের আগে স্থানীয় আবহাওয়া পরিস্থিতি ও পণ্যের লেবেল বিবেচনা করুন।" : "মাটির আর্দ্রতা পরীক্ষা করে প্রয়োজনমতো সেচের সময় ঠিক করুন।"}</p></div></section>
    </> : null}
  </>;
}

function DiseaseAssistant({ crop, setCrop, plantImage, plantFileName, fileInput, onImage, symptom, setSymptom, advice, loading, getAdvice }: { crop: string; setCrop: (value: string) => void; plantImage: string | null; plantFileName: string; fileInput: React.RefObject<HTMLInputElement | null>; onImage: (event: ChangeEvent<HTMLInputElement>) => void; symptom: string; setSymptom: (value: string) => void; advice: string; loading: boolean; getAdvice: () => void }) {
  return <>
    <ScreenTitle eyebrow="সতর্ক ও ব্যবহারযোগ্য সহায়তা" title="পাতার সমস্যা বুঝতে সহায়তা"><CropSelect value={crop} onChange={setCrop}/></ScreenTitle>
    <div className="notice info-notice"><ShieldCheck size={19}/><div><strong>নিরাপদ মূল্যায়ন</strong><p>এখানে ছবি আপনার ডিভাইসেই প্রিভিউ করা হয়। বর্তমান সংস্করণে ছবির স্বয়ংক্রিয় রোগ শনাক্তকরণ মডেল সংযুক্ত নেই; লক্ষণভিত্তিক AI পরামর্শ নিশ্চিত রোগ নির্ণয় নয়।</p></div></div>
    <section className="disease-layout"><div className="upload-card panel"><div className="upload-heading"><div className="metric-icon green"><ScanLine size={22}/></div><div><h2>পাতার ছবি যোগ করুন</h2><p>ভালো আলোতে, আক্রান্ত অংশটি কাছে থেকে তুলুন</p></div></div><input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" onChange={onImage} hidden/>{plantImage ? <div className="image-preview"><img src={plantImage} alt="আপলোড করা পাতার প্রিভিউ"/><button onClick={() => fileInput.current?.click()}><Upload size={15}/> ছবি বদলান</button><span>{plantFileName}</span></div> : <button className="upload-zone" onClick={() => fileInput.current?.click()}><span className="upload-icon"><Upload size={25}/></span><strong>ছবি নির্বাচন করুন</strong><small>JPG, PNG বা WebP · সর্বোচ্চ ৮ এমবি</small></button>}</div>
      <div className="diagnosis-card panel"><div className="panel-heading"><div><p className="section-kicker">লক্ষণ লিখুন</p><h2>প্রাথমিক মাঠ-পরামর্শ</h2></div><Bug size={23} className="muted-icon"/></div><label className="text-field"><span>আপনি কী দেখতে পাচ্ছেন?</span><textarea value={symptom} onChange={(event) => setSymptom(event.target.value)} placeholder="যেমন: পাতায় বাদামি দাগ, কুঁকড়ে যাচ্ছে, গাছ দুর্বল দেখাচ্ছে…" rows={5}/></label><button className="primary-button full-width" onClick={getAdvice} disabled={loading}>{loading ? <LoaderCircle size={17} className="spin"/> : <Sparkles size={17}/>} {loading ? "পরামর্শ তৈরি হচ্ছে" : "AI সহায়তা নিন"}</button><p className="tiny-note"><ShieldCheck size={14}/> জরুরি বা দ্রুত ছড়িয়ে পড়া সমস্যায় নিকটস্থ কৃষি অফিসে নমুনাসহ যোগাযোগ করুন।</p></div></section>
    {advice && <section className="advice-response"><Bot size={21}/><div><p className="section-kicker">ক্ষেতসাথীর পরামর্শ</p><div className="rich-text">{advice}</div></div></section>}
  </>;
}

function Chat({ messages, input, setInput, onSubmit, loading, error, districtName, setCrop, setActive }: { messages: ChatMessage[]; input: string; setInput: (value: string) => void; onSubmit: (event: FormEvent) => void; loading: boolean; error: string; districtName: string; setCrop: (value: string) => void; setActive: (value: Screen) => void }) {
  const suggestions = ["ধানের পাতায় দাগ হলে প্রথমে কী দেখব?", "বৃষ্টির আগে কীভাবে সেচ পরিকল্পনা করব?", "আলু সংরক্ষণে কী খেয়াল রাখা উচিত?"];
  return <>
    <ScreenTitle eyebrow="বাংলায় কৃষির কথা বলুন" title="AI কৃষি সহায়ক"><div className="ai-chip"><Bot size={17}/> ক্ষেতসাথী AI</div></ScreenTitle>
    <section className="chat-layout"><aside className="chat-context"><div className="assistant-avatar"><Bot size={25}/></div><h2>আজ কী নিয়ে ভাবছেন?</h2><p>ফসলের সাধারণ পরিচর্যা, আবহাওয়া বুঝে পরিকল্পনা এবং লক্ষণভিত্তিক নিরাপদ পরামর্শে আমি সাহায্য করতে পারি।</p><div className="context-item"><MapPin size={17}/><span>এলাকা<strong>{districtName}</strong></span></div><div className="context-item"><ShieldCheck size={17}/><span>উত্তর ভাষা<strong>বাংলা</strong></span></div><button onClick={() => { setCrop("ধান"); setActive("advice"); }} className="quiet-link">ফসলের গাইড দেখুন <ChevronRight size={15}/></button></aside>
      <div className="chat-panel panel"><div className="chat-head"><div><strong>ক্ষেতসাথী</strong><span><i className="status-dot"/> উত্তর দিতে প্রস্তুত</span></div><span>সাধারণ কৃষি সহায়তা</span></div><div className="chat-thread">{messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><div className="message-avatar">{message.role === "assistant" ? <Bot size={16}/> : <span>আপনি</span>}</div><p>{message.content}</p></div>)}{loading && <div className="message assistant"><div className="message-avatar"><Bot size={16}/></div><p className="typing"><i/><i/><i/></p></div>}</div>{error && <div className="chat-error"><FileWarning size={16}/><span>{error}</span></div>}<div className="suggestion-row">{suggestions.map((suggestion) => <button key={suggestion} onClick={() => setInput(suggestion)}>{suggestion}</button>)}</div><form className="chat-form" onSubmit={onSubmit}><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); onSubmit(event); } }} placeholder="আপনার প্রশ্ন লিখুন…" rows={1}/><button aria-label="বার্তা পাঠান" disabled={!input.trim() || loading}><Send size={19}/></button></form><p className="chat-disclaimer">AI-এর পরামর্শ সাধারণ তথ্য। রোগ, সার ও বালাই ব্যবস্থাপনায় স্থানীয় কৃষি বিশেষজ্ঞের পরামর্শ নিন।</p></div>
    </section>
  </>;
}

function CropAdvice({ crop, districtName, setCrop, selectDistrict, guide }: { crop: string; districtName: string; setCrop: (value: string) => void; selectDistrict: (value: string) => void; guide: typeof cropGuides[string] }) {
  return <>
    <ScreenTitle eyebrow="স্থান ও ফসলভিত্তিক পরিকল্পনা" title="ফসল পরামর্শ"><div className="screen-filters"><DistrictSelect value={districtName} onChange={selectDistrict}/><CropSelect value={crop} onChange={setCrop}/></div></ScreenTitle>
    <section className="advice-hero"><div><p className="section-kicker">{districtName} জেলার জন্য নির্বাচন করা হয়েছে</p><h2>{crop} চাষের মৌলিক নির্দেশনা</h2><p>এটি সাধারণ, বাংলাদেশ-প্রাসঙ্গিক পরিচর্যা নির্দেশনা। জমির মাটি, জাত, মৌসুম এবং স্থানীয় পরিস্থিতি অনুযায়ী কৃষি সম্প্রসারণ কর্মকর্তার পরামর্শকে অগ্রাধিকার দিন।</p></div><div className="advice-crop-symbol"><Leaf size={69}/><span>{crop}</span></div></section>
    <section className="guide-grid"><article><CalendarDays size={21}/><p>সময় ও মৌসুম</p><strong>{guide.season}</strong></article><article><Map size={21}/><p>জমি ও মাটি</p><strong>{guide.soil}</strong></article><article><Droplets size={21}/><p>পানি ব্যবস্থাপনা</p><strong>{guide.water}</strong></article></section>
    <section className="practice-panel panel"><div><p className="section-kicker">ভালো চাষের ভিত্তি</p><h2>মাঠে যা খেয়াল রাখবেন</h2></div><div className="practice-list"><div><span>০১</span><p>{guide.note}</p></div><div><span>০২</span><p>জমির ইতিহাস, মাটির পরীক্ষা এবং অনুমোদিত জাতের তথ্য নিয়ে স্থানীয় কৃষি অফিসের সঙ্গে পরিকল্পনা মিলিয়ে নিন।</p></div><div><span>০৩</span><p>{guide.warning}</p></div></div></section>
    <section className="help-callout"><div className="help-icon"><MessageCircle size={22}/></div><div><h2>আপনার জমির অবস্থা আলাদা?</h2><p>মাটি, সেচ বা পাতার লক্ষণ জানিয়ে ক্ষেতসাথী AI-এর কাছে সাধারণ পরামর্শ নিতে পারেন।</p></div><button className="secondary-button" onClick={() => document.querySelector<HTMLButtonElement>(".nav-item:nth-child(6)")?.click()}>AI-কে প্রশ্ন করুন <ChevronRight size={17}/></button></section>
  </>;
}
