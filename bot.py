import os
import asyncio
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
OWNER_ID = int(os.environ['OWNER_ID'])  # Your Telegram user ID

INTERVAL_FILE = "interval.txt"

# ===== Utils =====
def get_interval():
    try:
        with open(INTERVAL_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 3600  # default to 1 hour

def set_interval(seconds):
    with open(INTERVAL_FILE, "w") as f:
        f.write(str(seconds))

# ===== Handlers =====
async def set_interval_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /setinterval <seconds>")
        return

    try:
        seconds = int(context.args[0])
        set_interval(seconds)
        await update.message.reply_text(f"✅ Interval updated to {seconds} seconds.")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"👋 Hey! Your Telegram user ID is: {user_id}")

# ===== Background Posting Task =====
async def post_loop(bot: Bot):
    last_post_time = datetime.min
    while True:
        interval = get_interval()
        now = datetime.now()
        elapsed = (now - last_post_time).total_seconds()

        if elapsed >= interval:
            message = f"🕒 Automated post at {now.strftime('%H:%M:%S')}"
            await bot.send_message(chat_id=CHANNEL_ID, text=message)
            last_post_time = now

        await asyncio.sleep(1)  # check every second for more responsive updates


# ===== Main Entrypoint =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setinterval", set_interval_command))

    async def start_loop(application):
        asyncio.create_task(post_loop(application.bot))

    app.post_init = start_loop

    print("🚀 Bot is running...")
    app.run_polling()
