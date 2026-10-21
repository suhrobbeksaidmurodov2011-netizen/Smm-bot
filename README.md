# Telegram Do'kon Boti

Katalog, savatcha, buyurtma va admin panelga ega to'liq funksiyali Telegram do'kon boti.

## O'rnatish

1. **Bot tokenini oling**
   - Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
   - `/newbot` buyrug'ini yuboring, nomini kiriting
   - Sizga token beriladi (masalan: `123456:ABC-DEF...`)

2. **Admin ID raqamingizni bilib oling**
   - [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring
   - U sizning Telegram ID raqamingizni ko'rsatadi

3. **Konfiguratsiya**
   - `config.py` faylini oching
   - `BOT_TOKEN` ga tokeningizni qo'ying
   - `ADMIN_IDS` ro'yxatiga o'z ID raqamingizni qo'shing:
     ```python
     ADMIN_IDS = [123456789]
     ```

4. **Kutubxonalarni o'rnatish**
   ```bash
   pip install -r requirements.txt
   ```

5. **Botni ishga tushirish**
   ```bash
   python bot.py
   ```

## Foydalanuvchi buyruqlari

- `/start` — botni boshlash
- `/katalog` — mahsulotlarni ko'rish
- `/savat` — savatchani ko'rish va buyurtma berish
- `/buyurtmalarim` — oldingi buyurtmalar

## Admin buyruqlari

- `/admin` — admin panel yordami
- `/yangi_kategoriya <nomi>` — yangi kategoriya qo'shish
- `/yangi_mahsulot` — mahsulot qo'shish (bot savollar beradi)
- `/mahsulotlar` — barcha mahsulotlar ro'yxati
- `/ochirish <id>` — mahsulotni o'chirish
- `/buyurtmalar` — yangi (kutilayotgan) buyurtmalarni ko'rish va boshqarish

## Render.com'ga joylashtirish (bepul)

Bot `bot.py` ichida kichik HTTP health-check server bilan birga keladi — bu Render'ning bepul "Web Service" tarifida ishlashi uchun kerak (Render HTTP so'rovlarni kutadi).

### 1-qadam: Kodni GitHub'ga yuklash
1. [github.com](https://github.com)'da yangi repository yarating (masalan, `tgshop-bot`)
2. Shu papkadagi barcha fayllarni o'sha repoga yuklang (GitHub saytida "Add file → Upload files" orqali ham mumkin, Git bilishni talab qilmaydi)

### 2-qadam: Render'da Web Service yaratish
1. [render.com](https://render.com)'da ro'yxatdan o'ting (GitHub orqali kirish qulay)
2. **New +** → **Web Service** tanlang
3. GitHub repongizni ulang
4. Quyidagi sozlamalarni kiriting:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free
5. **Environment** bo'limida o'zgaruvchi qo'shing:
   - Key: `BOT_TOKEN`, Value: @BotFather'dan olgan tokeningiz
6. **Create Web Service** tugmasini bosing — Render avtomatik qurib, ishga tushiradi

### 3-qadam: Botni "uyg'oq" ushlab turish
Render'ning bepul tarifi 15 daqiqa so'rovsiz qolsa, xizmatni uxlatib qo'yadi. Buni oldini olish uchun:
1. [uptimerobot.com](https://uptimerobot.com)'da bepul hisob oching
2. **New Monitor** → turi: HTTP(s)
3. URL sifatida Render bergan manzilni kiriting (masalan, `https://tgshop-bot.onrender.com`)
4. Tekshirish oralig'ini 5 daqiqa qilib qo'ying

Shundan so'ng UptimeRobot har 5 daqiqada botingizga "signal" yuborib, uni doim uyg'oq ushlab turadi.

> **Eslatma:** Agar byudjetingiz bo'lsa, Render'ning pullik ($7/oy) "Background Worker" turi bundan ancha ishonchliroq — u uxlamaydi va health-check server kerak emas (shunda `bot.py`'dagi HTTP server qismini olib tashlashingiz ham mumkin).

## VPS'ga joylashtirish (muqobil variant)

### systemd bilan ishga tushirish (VPS uchun)

```ini
[Unit]
Description=Telegram Shop Bot
After=network.target

[Service]
WorkingDirectory=/path/to/tgshop
ExecStart=/usr/bin/python3 bot.py
Restart=always
Environment=BOT_TOKEN=your_token_here

[Install]
WantedBy=multi-user.target
```

## Eslatma: to'lov tizimlari

Hozirgi holatda bot to'lov usulini (naqd, karta, Click, Payme) faqat **tanlash** sifatida so'raydi — haqiqiy to'lov qabul qilmaydi. To'lovni tasdiqlash admin tomonidan qo'lda amalga oshiriladi (masalan, mijozga karta raqami yuboriladi, u o'tkazma qiladi, keyin admin buyurtmani tasdiqlaydi).

Agar avtomatik onlayn to'lov kerak bo'lsa, Click yoki Payme'ning rasmiy merchant API'sini ulashga alohida integratsiya kerak bo'ladi.

## Fayllar tuzilishi

```
tgshop/
├── bot.py              # Botni ishga tushiruvchi asosiy fayl
├── config.py            # Token, admin ID'lar, sozlamalar
├── database.py           # SQLite bilan ishlash
├── handlers_user.py       # Mijozlar uchun: katalog, savat, buyurtma
├── handlers_admin.py      # Admin panel: mahsulot va buyurtma boshqaruvi
├── requirements.txt
└── README.md
```
