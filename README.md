# Kalorix — Kaloriya Hisoblovchi Telegram Bot & Web App 🥗🤖

**Kalorix** — foydalanuvchilar yuborgan ovqat rasmini yoki matnli tavsifini OpenRouter AI (Vision/Text) orqali tahlil qilib, kaloriyasi, vazni hamda Oqsil / Yog' / Uglevod (BJU) miqdorini avtomatik hisoblab beruvchi Telegram bot va Web App platformasi.

---

## 🌟 Asosiy Xususiyatlar

- **📸 Rasm orqali AI tahlili:** Ovqat rasmi yuborilganda Pillow orqali siqilib, OpenRouter Vision modeliga yuboriladi va soniyalar ichida BJU ko'rsatkichlari aniqlanadi.
- **📝 Matn orqali kiritish:** `200g osh` yoki `1 ta olma` kabi matnli xabarlar filtrlangan holda AI text modeli orqali hisoblanadi.
- **⚡️ Smart UX (Loading State):** Rasm/matn yuborilganda dastlab `🔍 Tahlil qilinmoqda...` xabari yuborilib, natija kelishi bilan `edit_message_text` yordamida inline tugmalar (`Saqlash`, `Tuzatish`, `Bekor qilish`) bilan almashtiriladi.
- **🔥 Gamifikatsiya (Streak & Badges):** Har kuni ovqat kiritilganda uzluksiz streak davom etadi. "Birinchi qadam", "7 kunlik otash", "Gurman 50" kabi nishonlar va umumiy foydalanuvchilar reytingi taqdim etiladi.
- **🎯 Shaxsiy Maqsadlar:** Mifflin-St Jeor formulasi bo'yicha bo'y, vazn, yosh va jins asosida kunlik kaloriya normasi hisoblanadi.
- **⏰ Eslatmalar:** APScheduler yordamida nonushta (08:00), tushlik (13:00) va kechki ovqat (19:00) vaqtida avtomatik eslatmalar yuboriladi.
- **📱 Telegram Web App (Dashboard):** Sleek dark glassmorphism dizaynida Chart.js grafiklari, bugungi taomlar tarixi va statistikalar bilan ta'minlangan interaktiv dashboard.
- **💎 VIP & Limit Boshqaruvi:** Kunlik bepul so'rovlar limiti (`USER_FREE_DAILY_LIMIT`) hamda VIP foydalanuvchilar uchun cheksiz so'rovlar va kuchliroq modellar.
- **🐳 Docker readiness:** Healthcheck qo'shilgan PostgreSQL va backend servislari bilan `docker-compose` orqali bir bosqichda ishga tushadi.

---

## 🛠 Texnologiyalar

- **Bot Framework:** `aiogram 3.x` (Python async)
- **Backend Framework:** `FastAPI` + `Uvicorn`
- **ORM / Baza:** `SQLAlchemy 2.0 async` (SQLite & PostgreSQL)
- **AI Provider:** OpenRouter API (`google/gemma-4-31b-it:free`, `google/gemini-2.5-pro`, `openrouter/free` fallback)
- **Frontend:** Vanilla HTML5, CSS3 Glassmorphic Design, JavaScript (ES6+), Chart.js, Telegram WebApp SDK
- **Scheduler:** `APScheduler`
- **Konteynerizatsiya:** Docker & Docker Compose

---

## 🚀 Ishga Tushirish Qo'llanmasi

### 1. Mahalliy (Local) Ishga Tushirish

1. **Virtual muhit yaratish va kutubxonalarni o'rnatish:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

2. **Sozlamalarni kiritish (`.env`):**
   `.env.example` faylidan nusxa olib, `.env` faylini yarating va konfiguratsiyalarni kiriting:
   ```env
   BOT_TOKEN=777777777:ABC...
   OPENROUTER_API_KEY=sk-or-v1-...
   DATABASE_URL=sqlite+aiosqlite:///./kalorix.db
   WEB_APP_URL=http://localhost:8000/web_app
   USER_FREE_DAILY_LIMIT=10
   ```

3. **Ilovani ishga tushirish:**
   ```bash
   python main.py
   ```

### 2. Docker Compose Orqali Ishga Tushirish

```bash
docker-compose up --build -d
```

---

## 📄 Loyiha Strukturasi

```text
kaloriya/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── config.py
├── main.py
├── bot.py
├── pending.py
├── database/
│   ├── base.py
│   ├── session.py
│   └── models.py
├── services/
│   ├── ai_service.py
│   ├── user_service.py
│   ├── meal_service.py
│   ├── gamification_service.py
│   └── reminder_service.py
├── handlers/
│   ├── start.py
│   ├── photo.py
│   ├── text_meal.py
│   ├── inline.py
│   ├── stats.py
│   ├── goals.py
│   ├── leaderboard.py
│   └── settings.py
├── keyboards/
│   ├── reply.py
│   └── inline.py
├── states/
│   └── user_states.py
├── api/
│   ├── auth.py
│   └── dashboard.py
└── web_app/
    ├── index.html
    ├── styles.css
    └── app.js
```
