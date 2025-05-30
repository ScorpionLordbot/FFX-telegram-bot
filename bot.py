import os
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
OWNER_ID = int(os.environ['OWNER_ID'])  # Your Telegram user ID

INTERVAL_FILE = "interval.txt"

# Read interval from file
def get_interval():
    try:
        with open(INTERVAL_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 3600  # default 1 hour

# Write interval to file
def set_interval(seconds):
    with open(INTERVAL_FILE, "w") as f:
        f.write(str(seconds))

# Bot command: /setinterval 900
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

# Posting loop
async def post_loop(bot: Bot):
    while True:
        interval = get_interval()
        message = f"🕒 Automated post at {datetime.now().strftime('%H:%M:%S')}"
        await bot.send_message(chat_id=CHANNEL_ID, text=message)
        await asyncio.sleep(interval)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("setinterval", set_interval_command))

    # Start post loop in background
    asyncio.create_task(post_loop(app.bot))

    # Start listening for commands
    print("Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio

    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("setinterval", set_interval_command))
    bot_app.add_handler(CommandHandler("start", start))  # Optional for debugging

    # Start the background task (posting loop)
    async def start_loop():
        asyncio.create_task(post_loop(bot_app.bot))

    bot_app.post_init = start_loop

    # Run the bot (sync-safe)
    bot_app.run_polling()

