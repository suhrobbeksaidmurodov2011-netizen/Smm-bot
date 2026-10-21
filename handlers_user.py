from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters,
)
import database as db
from config import CURRENCY, PAYMENT_METHODS, ADMIN_IDS

# Checkout conversation states
ASK_NAME, ASK_PHONE, ASK_ADDRESS, ASK_PAYMENT = range(4)


def fmt_price(n):
    return f"{n:,}".replace(",", " ") + f" {CURRENCY}"


async def start(update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Assalomu alaykum! Do'kon botiga xush kelibsiz. 🛍\n\n"
        "/katalog — mahsulotlarni ko'rish\n"
        "/savat — savatchangizni ko'rish\n"
        "/buyurtmalarim — oldingi buyurtmalaringiz"
    )
    await update.message.reply_text(text)


async def show_categories(update, context: ContextTypes.DEFAULT_TYPE):
    categories = db.get_categories()
    if not categories:
        await update.effective_message.reply_text("Hozircha kategoriyalar mavjud emas.")
        return
    buttons = [[InlineKeyboardButton(c["name"], callback_data=f"cat:{c['id']}")] for c in categories]
    await update.effective_message.reply_text(
        "Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_products(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split(":")[1])
    products = db.get_products(category_id=category_id)
    if not products:
        await query.edit_message_text("Bu kategoriyada mahsulot yo'q.")
        return
    for p in products:
        caption = f"*{p['name']}*\n{p['description']}\n\nNarxi: {fmt_price(p['price'])}\nQolgan: {p['stock']} dona"
        buttons = [[InlineKeyboardButton("🛒 Savatchaga qo'shish", callback_data=f"add:{p['id']}")]]
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


async def add_to_cart_cb(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id = int(query.data.split(":")[1])
    product = db.get_product(product_id)
    if not product or product["stock"] <= 0:
        await query.answer("Afsuski, bu mahsulot qolmagan.", show_alert=True)
        return
    db.add_to_cart(query.from_user.id, product_id, 1)
    await query.answer("Savatchaga qo'shildi ✅")


async def show_cart(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    items = db.get_cart(user_id)
    if not items:
        await update.effective_message.reply_text("Savatchangiz bo'sh.")
        return
    lines = ["🛒 *Savatchangiz:*\n"]
    buttons = []
    total = 0
    for item in items:
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        lines.append(f"{item['name']} — {item['quantity']} x {fmt_price(item['price'])} = {fmt_price(subtotal)}")
        buttons.append([InlineKeyboardButton(f"❌ {item['name']}ni o'chirish", callback_data=f"rm:{item['cart_id']}")])
    lines.append(f"\n*Jami: {fmt_price(total)}*")
    buttons.append([InlineKeyboardButton("✅ Buyurtma berish", callback_data="checkout")])
    await update.effective_message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def remove_cart_item(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    cart_id = int(query.data.split(":")[1])
    db.remove_from_cart(cart_id)
    await query.answer("O'chirildi")
    await query.edit_message_text("Mahsulot savatchadan o'chirildi. /savat buyrug'i bilan qayta ko'ring.")


# ---------- Checkout conversation ----------

async def checkout_start(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    items = db.get_cart(user_id)
    if not items:
        await query.edit_message_text("Savatchangiz bo'sh.")
        return ConversationHandler.END
    await context.bot.send_message(
        chat_id=user_id,
        text="Buyurtmani rasmiylashtiramiz.\n\nIsm-familiyangizni kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


async def checkout_name(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting (masalan, +998901234567):")
    return ASK_PHONE


async def checkout_phone(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Yetkazib berish manzilini kiriting:")
    return ASK_ADDRESS


async def checkout_address(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    buttons = [[InlineKeyboardButton(label, callback_data=f"pay:{key}")] for key, label in PAYMENT_METHODS]
    await update.message.reply_text(
        "To'lov usulini tanlang:", reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ASK_PAYMENT


async def checkout_payment(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    payment_method = query.data.split(":")[1]
    user_id = query.from_user.id

    items_raw = db.get_cart(user_id)
    items = [dict(i) for i in items_raw]
    total = db.cart_total(user_id)

    order_id = db.create_order(
        user_id=user_id,
        username=query.from_user.username or "",
        full_name=context.user_data.get("full_name", ""),
        phone=context.user_data.get("phone", ""),
        address=context.user_data.get("address", ""),
        payment_method=payment_method,
        items=items,
        total=total,
    )
    db.clear_cart(user_id)

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            f"✅ Buyurtmangiz qabul qilindi!\n\n"
            f"Buyurtma raqami: #{order_id}\n"
            f"Jami summa: {fmt_price(total)}\n\n"
            f"Tez orada operatorimiz siz bilan bog'lanadi."
        ),
    )

    # Notify admins
    order_text = (
        f"🆕 Yangi buyurtma #{order_id}\n"
        f"Mijoz: {context.user_data.get('full_name','')} (@{query.from_user.username or '-'})\n"
        f"Tel: {context.user_data.get('phone','')}\n"
        f"Manzil: {context.user_data.get('address','')}\n"
        f"To'lov: {dict(PAYMENT_METHODS).get(payment_method, payment_method)}\n\n"
        + "\n".join(f"- {i['name']} x{i['quantity']}" for i in items)
        + f"\n\nJami: {fmt_price(total)}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=order_text)
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END


async def checkout_cancel(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Buyurtma bekor qilindi.")
    return ConversationHandler.END


async def my_orders(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    orders = db.get_orders(user_id=user_id)
    if not orders:
        await update.effective_message.reply_text("Sizda hali buyurtmalar yo'q.")
        return
    lines = []
    for o in orders[:10]:
        lines.append(f"#{o['id']} — {fmt_price(o['total'])} — holati: {o['status']} ({o['created_at']})")
    await update.effective_message.reply_text("\n".join(lines))


def get_checkout_conv_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(checkout_start, pattern="^checkout$")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_phone)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_address)],
            ASK_PAYMENT: [CallbackQueryHandler(checkout_payment, pattern="^pay:")],
        },
        fallbacks=[CommandHandler("bekor", checkout_cancel)],
    )


def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("katalog", show_categories))
    app.add_handler(CommandHandler("savat", show_cart))
    app.add_handler(CommandHandler("buyurtmalarim", my_orders))
    app.add_handler(CallbackQueryHandler(show_products, pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(add_to_cart_cb, pattern="^add:"))
    app.add_handler(CallbackQueryHandler(remove_cart_item, pattern="^rm:"))
    app.add_handler(get_checkout_conv_handler())
