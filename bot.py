import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ENV
TOKEN = "8175320891:AAFUY9TCDJBZuwFRIAZItgiYcCSCgj70DMI"
ADMIN_ID = "7558872588"

# Flask app (باش نفتح port)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Telegram bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبا! ابعث الطلب تاعك")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    # نبعث للادمين
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"طلب جديد من {user.first_name}:\n{text}"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1].file_id

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=f"صورة من {user.first_name}"
    )

def main():
    keep_alive()  # مهم 👈

    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app_bot.run_polling()

if name == "__main__":
    main()