import os
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "8175320891:AAFUY9TCDJBZuwFRIAZItgiYcCSCgj70DMI"
ADMIN_ID = "7558872588"

EURO = 250
COMMISSION = 1.15
FRAIS = 500
SHIPPING = 2000

PAYMENT_INFO = """
💳 معلومات الدفع:

🟢 CCP:
29337654 clé 89
SERINE BENALAGUE

🟢 BARIDI MOB:
00799999002933765497

📦 التوصيل:
الدفع يكون عند وصول المنتج مع شركة:
Nord et Ouest Express

📌 بعد الدفع، أرسلي صورة / فيديو / PDF وصل الدفع هنا لتأكيد الطلبية.
"""

user_data = {}

# Flask باش Render يشوف port مفتوح
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()


def calculate_price(price_euro):
    if price_euro <= 1.5:
        return 1000
    elif price_euro <= 2.5:
        return 1300
    elif price_euro <= 3.5:
        return 1700
    else:
        return int(price_euro * EURO * COMMISSION + FRAIS + SHIPPING)


def cart_text(cart):
    text = "🛍️ منتجات الطلبية:\n\n"
    total = 0

    for i, item in enumerate(cart, start=1):
        text += f"{i}. {item['price_euro']}€ → {item['total']} DA\n{item['link']}\n\n"
        total += item["total"]

    text += f"💰 المجموع: {total} DA"
    return text


def cart_buttons(cart):
    buttons = []

    for i in range(len(cart)):
        buttons.append([
            InlineKeyboardButton(f"🗑️ حذف المنتج {i+1}", callback_data=f"remove_{i}")
        ])

    buttons.append([
        InlineKeyboardButton("✅ تأكيد الطلبية", callback_data="confirm_order")
    ])
    buttons.append([
        InlineKeyboardButton("➕ إضافة منتجات أخرى", callback_data="add_more")
    ])
    buttons.append([
        InlineKeyboardButton("❌ إلغاء الطلبية", callback_data="cancel_order")
    ])

    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id] = {"step": None, "cart": []}

    await update.message.reply_text(
        ""Hi !🙋🏻‍♀️/باش نقص عليك مدة الانتظار 😍حطيتلك مساعد شخصي ليك 😲يشوفلك السعر ما عليك غير تبعثي رابط المننتج 😉و يلحقك السعر تلقائي / مرحبا بيك❤️"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {"step": None, "cart": []}

    if "shein" in text.lower():
        user_data[user_id]["current_link"] = text
        user_data[user_id]["step"] = "waiting_price"

        await update.message.reply_text(
            "تمام ✅\n"
            "أرسلي سعر المنتج بالأورو.\n\n"
            "مثال: 1.78 أو 1,78"
        )
        return

    if user_data[user_id].get("step") == "waiting_price":
        try:
            price_euro = float(text.replace(",", "."))
            total = calculate_price(price_euro)

            product = {
                "link": user_data[user_id].get("current_link", ""),
                "price_euro": price_euro,
                "total": total
            }

            user_data[user_id]["cart"].append(product)
            user_data[user_id]["step"] = None

            cart = user_data[user_id]["cart"]

            await update.message.reply_text(
                f"✅ تم إضافة المنتج للسلة.\n"
                f"💰 السعر: {total} DA\n"
                f"عدد المنتجات في السلة: {len(cart)}"
            )

            if len(cart) >= 3:
                await update.message.reply_text(
                    cart_text(cart) + "\n\nهل تريدين تأكيد الطلبية؟",
                    reply_markup=cart_buttons(cart)
                )
            else:
                await update.message.reply_text(
                    "أرسلي رابط منتج آخر أو اكتبي /cart لعرض السلة."
                )

        except:
            await update.message.reply_text(
                "من فضلك أرسلي السعر كرقم فقط.\nمثال: 1.78 أو 1,78"
            )

        return

    if user_data[user_id].get("step") == "waiting_info":
        user_data[user_id]["client_info"] = text
        user_data[user_id]["step"] = "waiting_receipt"

        await update.message.reply_text(
            "✅ تم استلام معلوماتك.\n\n" + PAYMENT_INFO
        )
        return

    await update.message.reply_text("أرسلي رابط منتج Shein أولًا 🛍️")


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data or len(user_data[user_id]["cart"]) == 0:
        await update.message.reply_text("السلة فارغة.")
        return

    cart = user_data[user_id]["cart"]
    await update.message.reply_text(
        cart_text(cart),
        reply_markup=cart_buttons(cart)
    )


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data:
        await update.message.reply_text("اكتبي /start للبدء.")
        return

    if user_data[user_id].get("step") != "waiting_receipt":
        await update.message.reply_text("تم استلام الملف، لكن لا توجد طلبية قيد التأكيد.")
        return

    cart = user_data[user_id].get("cart", [])
    client_info = user_data[user_id].get("client_info", "لم تُرسل المعلومات.")

    username = update.message.from_user.username
    full_name = update.message.from_user.full_name

    order_summary = (
        "📦 طلبية جديدة مؤكدة\n\n"
        f"👤 الزبونة: {full_name}\n"
        f"🔗 Username: @{username if username else 'لا يوجد'}\n"
        f"🆔 Telegram ID: {user_id}\n\n"
        f"📋 معلومات الزبونة:\n{client_info}\n\n"
        f"{cart_text(cart)}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=order_summary)

    if update.message.photo:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption="🧾 وصل الدفع"
        )
    elif update.message.video:
        await context.bot.send_video(
            chat_id=ADMIN_ID,
            video=update.message.video.file_id,
            caption="🧾 وصل الدفع"
        )
    elif update.message.document:
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=update.message.document.file_id,
            caption="🧾 وصل الدفع"
        )

    await update.message.reply_text(
        "✅ تم إرسال طلبك للتأكيد.\n"
        "سنتواصل معك بعد مراجعة وصل الدفع."
    )

    user_data[user_id] = {"step": None, "cart": []}


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {"step": None, "cart": []}

    cart = user_data[user_id]["cart"]
    data = query.data

    if data.startswith("remove_"):
        index = int(data.split("_")[1])

        if 0 <= index < len(cart):
            cart.pop(index)

        if len(cart) == 0:
            await query.message.reply_text("السلة فارغة.")
        else:
            await query.message.reply_text(
                cart_text(cart),
                reply_markup=cart_buttons(cart)
            )

    elif data == "confirm_order":
        if len(cart) == 0:
            await query.message.reply_text("السلة فارغة.")
            return

        user_data[user_id]["step"] = "waiting_info"

        await query.message.reply_text(
            cart_text(cart) +
            "\n\n✅ لتأكيد الطلبية، أرسلي المعلومات التالية في رسالة واحدة:\n\n"
            "الاسم:\n"
            "اللقب:\n"
            "رقم الهاتف:\n"
            "الولاية:\n"
            "البلدية:\n"
        )

    elif data == "add_more":
        await query.message.reply_text("أرسلي رابط منتج Shein جديد.")

    elif data == "cancel_order":
        user_data[user_id]["cart"] = []
        user_data[user_id]["step"] = None
        await query.message.reply_text("❌ تم إلغاء الطلبية.")


def main():
    keep_alive()

    bot_app = ApplicationBuilder().token(TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("cart", show_cart))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    bot_app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_receipt))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    bot_app.run_polling()


if __name__ == "__main__":
    main()