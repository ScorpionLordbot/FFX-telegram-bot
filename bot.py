import os
import asyncio
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Environment Variables ===
# These should be defined in your Railway/hosting environment
BOT_TOKEN = os.environ['BOT_TOKEN']             # Your bot's token from @BotFather
CHANNEL_ID = os.environ['CHANNEL_ID']           # Target channel ID (must start with -100 for supergroups)
OWNER_ID = int(os.environ['OWNER_ID'])          # Telegram user ID of the bot owner (authorized user)

# === Local File Constants ===
INTERVAL_FILE = "interval.txt"                  # Stores how often the bot should post (in seconds)
MESSAGE_FILE = "message.txt"                    # Stores the message content to be posted

# ===== Utility Functions =====

# Reads the posting interval from file or returns a default (3600 seconds = 1 hour)
def get_interval():
    try:
        with open(INTERVAL_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 3600

# Writes the new interval to file
def set_interval(seconds):
    with open(INTERVAL_FILE, "w") as f:
        f.write(str(seconds))

# Reads the automated message from file
def get_message():
    try:
        with open(MESSAGE_FILE, "r") as f:
            return f.read().strip()
    except:
        return "🕒 Default automated message."

# Writes a new automated message to file
def set_message(new_msg):
    with open(MESSAGE_FILE, "w") as f:
        f.write(new_msg.strip())

# ===== Command Handlers =====

# /setinterval <seconds> — Updates the posting interval
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

# /setmessage <text> — Sets the message that will be posted automatically
async def set_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /setmessage <your message>")
        return

    new_msg = " ".join(context.args)
    set_message(new_msg)
    await update.message.reply_text("✅ Message updated successfully!")

# /viewmessage — Displays the current automated message
async def view_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    current_message = get_message()
    await update.message.reply_text(f"📝 Current message:\n\n{current_message}")

# /start — Simple command to identify the user ID (useful for setup/debug)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"👋 Hey! Your Telegram user ID is: {user_id}")

# ===== Background Posting Loop =====

# Continuously checks whether it's time to post a message
async def post_loop(bot: Bot):
    last_post_time = datetime.min  # Start time

    while True:
        interval = get_interval()
        now = datetime.now()
        elapsed = (now - last_post_time).total_seconds()

        # If it's time to post, send the message
        if elapsed >= interval:
            message = get_message()
            await bot.send_message(chat_id=CHANNEL_ID, text=message)
            last_post_time = now

        await asyncio.sleep(1)  # Check every second for more accuracy

# ===== Main Entrypoint =====
if __name__ == "__main__":
    # Create the Telegram bot application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setinterval", set_interval_command))
    app.add_handler(CommandHandler("setmessage", set_message_command))
    app.add_handler(CommandHandler("viewmessage", view_message_command))

    # Run the background posting loop once the bot is initialized
    async def start_loop(application):
        asyncio.create_task(post_loop(application.bot))

    app.post_init = start_loop

    # Start polling for updates
    print("🚀 Bot is running...")
    app.run_polling()
