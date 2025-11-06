import os
import asyncio
from threading import Thread
from flask import Flask
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Muhit o'zgaruvchilarini o'qish
OPENAI_API_KEY = os.getenv("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")
TELEGRAM_BOT_TOKEN = os.getenv("8449482619:AAEctGWUUfGZtCni1QNgiDxT8W8kdhYWqB0")

if not OPENAI_API_KEY or not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("OPENAI_API_KEY va TELEGRAM_BOT_TOKEN muhit o'zgaruvchilarini o'rnating.")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "Siz foydalanuvchiga o'zbek tilida, sodda va aniq javob beradigan yordamchisiz. "
    "O'rinsiz izoh bermang, kerak bo'lsa qisqa ro'yxatlar bilan tushuntiring. "
    "Agar savol trading yoki XAUUSD bo'lsa, xavf ogohlantirishini ham eslating."
)

# --- Flask orqali web server (UptimeRobot uchun) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
# ----------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Men ChatGPT botman. Menga savol yozing — imkon qadar aniq javob beraman.\n"
        "Buyruqlar: /start, /help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Menga oddiy xabar yuboring. Masalan:\n"
        "'XAUUSD uchun London sessiya senariylari?' yoki\n"
        "'Python-da fayl qanday o'qiladi?'."
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = (update.message.text or "").strip()
    if not user_text:
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        answer = resp.choices[0].message.content.strip()

    except Exception as e:
        answer = f"Uzr, hozir javob yaratishda muammo yuz berdi. Xatolik: {type(e).__name__}"

    CHUNK = 3500
    for i in range(0, len(answer), CHUNK):
        await update.message.reply_text(answer[i:i+CHUNK])

def main():
    keep_alive()  # <-- Flask serverni ishga tushiramiz
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    application.run_polling(close_loop=False)

if __name__ == "__main__":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # Windows uchun
    except Exception:
        pass
    main()
