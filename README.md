# Smart Krishi Buddhimotta 🌾

বাংলাদেশি কৃষকের জন্য বাংলা-ভিত্তিক কৃষি সহায়তা অ্যাপ। **Technology should empower those who feed nations.** বর্তমান ফ্রন্টএন্ডটি `ui-smart-krishi-buddhimotta/`-র Next.js UI; **ফসল পরামর্শ** গাইডসহ এর নকশা ও মেনু অক্ষুণ্ণ রাখা হয়েছে।

## কীভাবে কাজ করে

- **Next.js (Vercel):** UI, Open-Meteo আবহাওয়া API route, OpenStreetMap অবস্থান/মানচিত্র, Telegram webhook, এবং Python API-র server-side proxy।
- **FastAPI (Render বা অন্য Python host):** Groq বাংলা চ্যাট, রোগের ছবির inference, এবং মূল্য-পূর্বাভাসের prototype endpoint।
- **রোগের ছবি:** drop/gallery/camera থেকে ছবি দিলেই স্বয়ংক্রিয়ভাবে বিশ্লেষণ হয়। `GROQ_API_KEY` থাকলে Qwen multimodal vision ছবিটি Groq-এ পাঠিয়ে ফসল/রোগের একটি ছোট, অনিশ্চিত প্রাথমিক অনুমান দেয়; এই ছবি-স্থানান্তর UI-তে জানানো হয়। Qwen না থাকলে/ব্যর্থ হলে স্থানীয় ResNet9-এর ৩৮-শ্রেণির checkpoint fallback; compact `.pth` না চললে bundled full-model `.pth`-ও চেষ্টা হয়। স্থানীয় অনুমান একা pesticide product/dose দেখায় না; স্থানীয় মডেল না চললেও কনফিগার করা Qwen ছবির পথ হিসেবে কাজ করতে পারে। ঐচ্ছিক দীর্ঘ ব্যাখ্যা আলাদা text-only Groq call, ডিফল্টে GPT-OSS 20B এবং Llama 3.1 8B fallback। কোনো মডেলই নিশ্চিত রোগনির্ণয় নয়। চিকিৎসার তথ্য server-side, সংকীর্ণ DAE PPW allow-list থেকে; সঠিক crop–disease label match না থাকলে brand/dose/application method দেখানো হয় না। PPW record বাজারে মজুত বা বর্তমান label-এর নিশ্চয়তা নয়।
- **মূল্য:** `bd_crop_price_data.csv`-র নমুনা দিয়ে backend-এর ১৪ দিনের পরীক্ষামূলক simulation; CSV-র তারিখ ১৮ মে ২০২৫-এ শেষ। ফল **লাইভ, সরকারি বা যাচাইকৃত দাম/পূর্বাভাস নয়**। CSV-তে ফসলের সারি না থাকলে স্পষ্টভাবে demo baseline ব্যবহৃত হয়। বাজারদরের স্ক্রিনেও কেবল prototype data দেখানো হয়।
- **ফসল পরামর্শ:** বিদ্যমান ২১টি ফসলের স্থানীয় গাইড; বাইরের AI বা database ছাড়াই চলে।
- **Weather/map:** keyless Open-Meteo forecast এবং OpenStreetMap; API key লাগে না।
- **Telegram:** `/start` বা `/help`-এ স্বাগতম বার্তা ও deployed app-এর button।

কোনো PostgreSQL/database লাগবে না। API key বা bot token browser-এ প্রকাশ করবেন না।

## চালানো ও deploy

- Local development, Vercel, Render, Telegram webhook, environment variables এবং free-tier সীমাবদ্ধতার ধাপে-ধাপে নির্দেশনা: **[DEPLOYMENT.md](DEPLOYMENT.md)**।
- Python API dependency list: `backend/requirements.txt`।
- Render Blueprint: `render.yaml`।
- Safe variable-name templates: `backend/.env.example`, `ui-smart-krishi-buddhimotta/.env.example` (এগুলোতে কোনো real secret নেই)।

## Attribution ও সীমাবদ্ধতা

- মূল disease model/ওজন ও কিছু কৃষি সহায়তা উপাদান পূর্ববর্তী [Agri-Smart-BD](https://github.com/NawrizTurjo/Agri-Smart-BD) কাজ থেকে এসেছে; প্রকল্পের `LICENSE` ও মূল notices দেখুন।
- রোগ মডেলের শ্রেণি PlantVillage training labels-ভিত্তিক; বাংলাদেশের সব ফসল/রোগ অন্তর্ভুক্ত নয়। স্কোর calibrated probability বা নিশ্চিত diagnosis নয়।
- মূল্য CSV-র নাম/তারিখ বাংলাদেশি live market feed-এর প্রমাণ নয়। বিক্রি, ক্রয় বা চাষের সিদ্ধান্তে স্থানীয় বাজার ও কৃষি কর্মকর্তার তথ্য যাচাই করুন।
- আবহাওয়া পূর্বাভাস, নিশ্চয়তা নয়।

MIT License — see [`LICENSE`](LICENSE); inherited components retain their respective attribution.
