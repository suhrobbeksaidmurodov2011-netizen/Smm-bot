import os

# Bot tokenini @BotFather'dan oling va shu yerga qo'ying
# yoki muhit o'zgaruvchisi (environment variable) sifatida bering: BOT_TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN", "BOT_TOKENINGIZNI_SHU_YERGA_QOYING")

# Admin foydalanuvchilarning Telegram ID raqamlari (ro'yxat)
# O'z ID raqamingizni bilish uchun @userinfobot ga /start yuboring
ADMIN_IDS = [
    # 123456789,
]

DB_PATH = "shop.db"

CURRENCY = "so'm"

PAYMENT_METHODS = [
    ("cash", "Naqd pul (yetkazib berishda)"),
    ("card", "Karta orqali o'tkazma"),
    ("click", "Click"),
    ("payme", "Payme"),
]
