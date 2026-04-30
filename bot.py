import os
import unicodedata
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

TOKEN = os.getenv("8175320891:AAFUY9TCDJBZuwFRIAZItgiYcCSCgj70DMI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

EURO = 270
COMMISSION = 1.15
FRAIS = 500
SHIPPING_FRANCE = 2000

DELIVERY_PRICES = {
    "setif": 600, "bordj bou arreridj": 700, "alger": 600, "annaba": 700,
    "batna": 700, "bejaia": 700, "blida": 700, "bouira": 700,
    "boumerdes": 700, "constantine": 650, "jijel": 700, "khenchela": 800,
    "medea": 800, "mila": 800, "msila": 700, "oum el bouaghi": 800,
    "skikda": 800, "tipaza": 700, "tizi ouzou": 700, "el tarf": 850,
    "guelma": 850, "souk ahras": 850, "tebessa": 850, "ain defla": 800,
    "chlef": 700, "mostaganem": 800, "oran": 700, "ain temouchent": 800,
    "mascara": 800, "relizane": 800, "sidi bel abbes": 800, "tissemsilt": 800,
    "saida": 900, "tiaret": 800, "tlemcen": 800, "biskra": 900,
    "djelfa": 900, "laghouat": 900, "el oued": 1000, "ghardaia": 1000,
    "ouargla": 1000, "touggourt": 1000, "bechar": 1200, "beni abbes": 1200,
    "el bayadh": 1200, "naama": 1200, "adrar": 1500, "timimoun": 1500,
    "tindouf": 1500, "in salah": 1850, "tamanrasset": 2000, "illizi": 2000
}

WILAYA_ALIASES = {
    "سطيف": "setif", "sétif": "setif",
    "برج بوعريريج": "bordj bou arreridj", "bordj": "bordj bou arreridj",
    "الجزائر": "alger", "algiers": "alger",
    "عنابة": "annaba",
    "باتنة": "batna",
    "بجاية": "bejaia", "béjaïa": "bejaia",
    "البليدة": "blida",
    "البويرة": "bouira",
    "بومرداس": "boumerdes", "boumerdès": "boumerdes",
    "قسنطينة": "constantine",
    "جيجل": "jijel",
    "خنشلة": "khenchela",
    "المدية": "medea", "médéa": "medea",
    "ميلة": "mila",
    "المسيلة": "msila", "m'sila": "msila",
    "أم البواقي": "oum el bouaghi", "ام البواقي": "oum el bouaghi",
    "سكيكدة": "skikda",
    "تيبازة": "tipaza",
    "تيزي وزو": "tizi ouzou",
    "الطارف": "el tarf",
    "قالمة": "guelma",
    "سوق أهراس": "souk ahras", "سوق اهراس": "souk ahras",
    "تبسة": "tebessa", "tébessa": "tebessa",
    "عين الدفلى": "ain defla",
    "الشلف": "chlef",
    "مستغانم": "mostaganem",
    "وهران": "oran",
    "عين تموشنت": "ain temouchent",
    "معسكر": "mascara",
    "غليزان": "relizane",
    "سيدي بلعباس": "sidi bel abbes",
    "تيسمسيلت": "tissemsilt",
    "سعيدة": "saida",
    "تيارت": "tiaret",
    "تلمسان": "tlemcen",
    "بسكرة": "biskra",
    "الجلفة": "djelfa",
    "الأغواط": "laghouat", "الاغواط": "laghouat",
    "الوادي": "el oued",
    "غرداية": "ghardaia",
    "ورقلة": "ouargla",
    "تقرت": "touggourt",
    "بشار": "bechar",
    "بني عباس": "beni abbes",
    "البيض": "el bayadh",
    "النعامة": "naama",
    "أدرار": "adrar", "ادرار": "adrar",
    "تيميمون": "timimoun",
    "تندوف": "tindouf",
    "عين صالح": "in salah",
    "تمنراست": "tamanrasset",
    "إليزي": "illizi", "اليزي": "illizi"
}

PAYMENT_INFO = """
💳 معلومات الدفع:

🟢 CCP:
29337654 clé 89
SERINE BENALAGUE

🟢 BARIDI MOB:
00799999002933765497

📦 التوصيل:
التوصيل يكون للمنزل حسب الولاية.

📌 بعد الدفع، أرسلي صورة / فيديو / PDF وصل الدفع هنا لتأكيد الطلبية.
"""

user_data = {}

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()

def normalize(text):
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("’", "'").replace("`", "'")
    return text

def find_wilaya(text):
    clean = normalize(text)

    for name in DELIVERY_PRICES:
        if name in clean:
            return name

    for alias, canonical in WILAYA_ALIASES.items():
        if normalize(alias) in clean:
            return canonical

    return None

def calculate_price(price_euro):
    if price_euro <= 1.5:
        return 1000
    elif price_euro <= 2.5:
        return 1300
    elif price_euro <= 3.5:
        return 1700
    else:
        return int(price_euro * EURO * COMMISSION + FRAIS + SHIPPING_FRANCE)

def products_total(cart):
    return sum(item["total"] for item in cart)

def cart_text(user_id):
    cart = user_data[user_id]["cart"]
    text = "🛍️ منتجات الطلبية:\n\n"
    total_products = 0

    for i, item in enumerate(cart, start=1):
        text += f"{i}. {item['price_euro']}€ → {item['total']} DA\n{item['link']}\n\n"
        total_products += item["total"]

    text += f"💰 مجموع المنتجات: {total_products} DA"

    delivery = user_data[user_id].get("delivery_price")
    wilaya = user_data[user_id].get("wilaya")

    if delivery is not None:
        text += f"\n🚚 توصيل للمنزل - {wilaya.title()}: {delivery} DA"
        text += f"\n✅ المجموع النهائي: {total_products + delivery} DA"

    return text

def cart_buttons(cart):
    buttons = []

    for i in range(len(cart)):
        buttons.append([
            InlineKeyboardButton(f"🗑️ حذف المنتج {i+1}", callback_data=f"remove_{i}")
        ])

    buttons.append([InlineKeyboardButton("✅ تأكيد الطلبية", callback_data="confirm_order")])
    buttons.append([InlineKeyboardButton("➕ إضافة منتجات أخرى", callback_data="add_more")])
    buttons.append([InlineKeyboardButton("❌ إلغاء الطلبية", callback_data="cancel_order")])

    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id] = {
        "step": None,
        "cart": [],
        "delivery_price": None,
        "wilaya": None
    }

    await update.message.reply_text("""👋 مرحبا بيك في Trend it 🛍️

باش نسهلو عليك الطلب من SHEIN 😍
حطينا لك مساعد شخصي 🤖

💰 يعطيك السعر مباشرة بالدينار
📦 يحسبلك الطلبية كاملة
🚚 يحسبلك التوصيل للمنزل حسب الولاية

📎 ابعتي رابط المنتج من SHEIN للبدء
💶 ومن بعد ابعتي السعر بالأورو
""")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {
            "step": None,
            "cart": [],
            "delivery_price": None,
            "wilaya": None
        }

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
                    cart_text(user_id) + "\n\nهل تريدين تأكيد الطلبية؟",
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

        wilaya = find_wilaya(text)

        if wilaya is None:
            user_data[user_id]["step"] = "waiting_wilaya"
            await update.message.reply_text(
                "ما قدرتش نعرف الولاية من المعلومات.\n"
                "من فضلك اكتبي الولاية فقط، بالعربية أو الفرنسية.\n\n"
                "مثال: الجزائر / Alger / Oran / وهران"
            )
            return

        user_data[user_id]["wilaya"] = wilaya
        user_data[user_id]["delivery_price"] = DELIVERY_PRICES[wilaya]
        user_data[user_id]["step"] = "waiting_receipt"

        await update.message.reply_text(
            cart_text(user_id) + "\n\n" + PAYMENT_INFO
        )
        return

    if user_data[user_id].get("step") == "waiting_wilaya":
        wilaya = find_wilaya(text)

        if wilaya is None:
            await update.message.reply_text(
                "❌ الولاية غير مفهومة.\n"
                "اكتبيها بالعربية أو الفرنسية مثل: Alger / الجزائر / Oran / وهران"
            )
            return

        user_data[user_id]["wilaya"] = wilaya
        user_data[user_id]["delivery_price"] = DELIVERY_PRICES[wilaya]
        user_data[user_id]["step"] = "waiting_receipt"

        await update.message.reply_text(
            cart_text(user_id) + "\n\n" + PAYMENT_INFO
        )
        return

    await update.message.reply_text("أرسلي رابط منتج Shein أولًا 🛍️")

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data or len(user_data[user_id]["cart"]) == 0:
        await update.message.reply_text("السلة فارغة.")
        return

    await update.message.reply_text(
        cart_text(user_id),
        reply_markup=cart_buttons(user_data[user_id]["cart"])
    )

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data or user_data[user_id].get("step") != "waiting_receipt":
        await update.message.reply_text("تم استلام الملف، لكن لا توجد طلبية قيد التأكيد.")
        return

    username = update.message.from_user.username
    full_name = update.message.from_user.full_name
    client_info = user_data[user_id].get("client_info", "لم تُرسل المعلومات.")

    order_summary = (
        "📦 طلبية جديدة مؤكدة\n\n"
        f"👤 الزبونة: {full_name}\n"
        f"🔗 Username: @{username if username else 'لا يوجد'}\n"
        f"🆔 Telegram ID: {user_id}\n\n"
        f"📋 معلومات الزبونة:\n{client_info}\n\n"
        f"{cart_text(user_id)}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=order_summary)

    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption="🧾 وصل الدفع")
    elif update.message.video:
        await context.bot.send_video(chat_id=ADMIN_ID, video=update.message.video.file_id, caption="🧾 وصل الدفع")
    elif update.message.document:
        await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption="🧾 وصل الدفع")

    await update.message.reply_text(
        "✅ تم إرسال طلبك للتأكيد.\n"
        "سنتواصل معك بعد مراجعة وصل الدفع."
    )

    user_data[user_id] = {
        "step": None,
        "cart": [],
        "delivery_price": None,
        "wilaya": None
    }

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {
            "step": None,
            "cart": [],
            "delivery_price": None,
            "wilaya": None
        }

    cart = user_data[user_id]["cart"]
    data = query.data

    if data.startswith("remove_"):
        index = int(data.split("_")[1])

        if 0 <= index < len(cart):
            cart.pop(index)

        if len(cart) == 0:
            await query.message.reply_text("السلة فارغة.")
        else:
            await query.message.reply_text(cart_text(user_id), reply_markup=cart_buttons(cart))

    elif data == "confirm_order":
        if len(cart) == 0:
            await query.message.reply_text("السلة فارغة.")
            return

        user_data[user_id]["step"] = "waiting_info"

        await query.message.reply_text(
            cart_text(user_id) +
            "\n\n✅ لتأكيد الطلبية، أرسلي المعلومات التالية في رسالة واحدة:\n\n"
            "الاسم:\n"
            "اللقب:\n"
            "رقم الهاتف:\n"
            "الولاية:\n"
            "البلدية:\n"
            "العنوان الكامل:\n"
        )

    elif data == "add_more":
        await query.message.reply_text("أرسلي رابط منتج Shein جديد.")

    elif data == "cancel_order":
        user_data[user_id] = {
            "step": None,
            "cart": [],
            "delivery_price": None,
            "wilaya": None
        }
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