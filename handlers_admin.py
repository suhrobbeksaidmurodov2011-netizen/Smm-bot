from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters,
)
import database as db
from config import ADMIN_IDS, CURRENCY, PAYMENT_METHODS

# Add-product conversation states
AP_CATEGORY, AP_NAME, AP_DESC, AP_PRICE, AP_STOCK = range(5)


def fmt_price(n):
    return f"{n:,}".replace(",", " ") + f" {CURRENCY}"


def admin_only(func):
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            if update.message:
                await update.message.reply_text("Bu buyruq faqat adminlar uchun.")
            return ConversationHandler.END if "Conversation" in func.__qualname__ else None
        return await func(update, context, *args, **kwargs)
    return wrapper


@admin_only
async def admin_help(update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👑 *Admin panel*\n\n"
        "/yangi_kategoriya <nomi> — kategoriya qo'shish\n"
        "/yangi_mahsulot — mahsulot qo'shish (suhbat orqali)\n"
        "/mahsulotlar — barcha mahsulotlar\n"
        "/ochirish <id> — mahsulotni o'chirish\n"
        "/buyurtmalar — yangi buyurtmalar ro'yxati"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@admin_only
async def new_category(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /yangi_kategoriya <nomi>")
        return
    name = " ".join(context.args)
    db.add_category(name)
    await update.message.reply_text(f"Kategoriya qo'shildi: {name}")


@admin_only
async def list_products(update, context: ContextTypes.DEFAULT_TYPE):
    products = db.get_products(active_only=False)
    if not products:
        await update.message.reply_text("Mahsulotlar yo'q.")
        return
    lines = [f"#{p['id']} {p['name']} — {fmt_price(p['price'])} — qolgan: {p['stock']}"
             + ("" if p["active"] else " (nofaol)") for p in products]
    await update.message.reply_text("\n".join(lines))


@admin_only
async def delete_product_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /ochirish <mahsulot_id>")
        return
    try:
        product_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID raqam bo'lishi kerak.")
        return
    db.delete_product(product_id)
    await update.message.reply_text(f"Mahsulot #{product_id} o'chirildi.")


@admin_only
async def list_orders(update, context: ContextTypes.DEFAULT_TYPE):
    orders = db.get_orders(status="kutilmoqda")
    if not orders:
        await update.message.reply_text("Yangi buyurtmalar yo'q.")
        return
    for o in orders[:15]:
        text = (
            f"#{o['id']} — {o['full_name']} — {o['phone']}\n"
            f"Manzil: {o['address']}\n"
            f"To'lov: {dict(PAYMENT_METHODS).get(o['payment_method'], o['payment_method'])}\n"
            f"Jami: {fmt_price(o['total'])}\n"
            f"Sana: {o['created_at']}"
        )
        buttons = [[
            InlineKeyboardButton("✅ Bajarildi", callback_data=f"ord_done:{o['id']}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"ord_cancel:{o['id']}"),
        ]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def order_status_cb(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("Ruxsat yo'q.", show_alert=True)
        return
    action, order_id = query.data.split(":")
    order_id = int(order_id)
    status = "bajarildi" if action == "ord_done" else "bekor qilindi"
    db.update_order_status(order_id, status)
    await query.answer(f"Buyurtma holati: {status}")
    await query.edit_message_text(query.message.text + f"\n\n➡️ Holat: {status}")


# ---------- Add product conversation ----------

@admin_only
async def add_product_start(update, context: ContextTypes.DEFAULT_TYPE):
    categories = db.get_categories()
    if not categories:
        await update.message.reply_text(
            "Avval kategoriya yarating: /yangi_kategoriya <nomi>"
        )
        return ConversationHandler.END
    buttons = [[InlineKeyboardButton(c["name"], callback_data=f"apcat:{c['id']}")] for c in categories]
    await update.message.reply_text("Qaysi kategoriyaga qo'shamiz?", reply_markup=InlineKeyboardMarkup(buttons))
    return AP_CATEGORY


async def add_product_category(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ap_category"] = int(query.data.split(":")[1])
    await query.edit_message_text("Mahsulot nomini kiriting:")
    return AP_NAME


async def add_product_name(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ap_name"] = update.message.text
    await update.message.reply_text("Tavsifini kiriting (yoki '-' agar bo'lmasa):")
    return AP_DESC


async def add_product_desc(update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text
    context.user_data["ap_desc"] = "" if desc == "-" else desc
    await update.message.reply_text("Narxini kiriting (faqat raqam, so'mda):")
    return AP_PRICE


async def add_product_price(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", ""))
    except ValueError:
        await update.message.reply_text("Iltimos, narxni raqam ko'rinishida kiriting.")
        return AP_PRICE
    context.user_data["ap_price"] = price
    await update.message.reply_text("Omborda nechta dona bor?")
    return AP_STOCK


async def add_product_stock(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stock = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Iltimos, miqdorni raqam ko'rinishida kiriting.")
        return AP_STOCK
    ud = context.user_data
    db.add_product(ud["ap_category"], ud["ap_name"], ud["ap_desc"], ud["ap_price"], stock)
    await update.message.reply_text(f"✅ '{ud['ap_name']}' mahsulot sifatida qo'shildi.")
    ud.clear()
    return ConversationHandler.END


async def add_product_cancel(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END


def get_add_product_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("yangi_mahsulot", add_product_start)],
        states={
            AP_CATEGORY: [CallbackQueryHandler(add_product_category, pattern="^apcat:")],
            AP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            AP_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_desc)],
            AP_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            AP_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_stock)],
        },
        fallbacks=[CommandHandler("bekor", add_product_cancel)],
    )


def register_admin_handlers(app):
    app.add_handler(CommandHandler("admin", admin_help))
    app.add_handler(CommandHandler("yangi_kategoriya", new_category))
    app.add_handler(CommandHandler("mahsulotlar", list_products))
    app.add_handler(CommandHandler("ochirish", delete_product_cmd))
    app.add_handler(CommandHandler("buyurtmalar", list_orders))
    app.add_handler(CallbackQueryHandler(order_status_cb, pattern="^ord_(done|cancel):"))
    app.add_handler(get_add_product_conv_handler())
