import os
import asyncio
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Environment Variables ===
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
OWNER_ID = int(os.environ['OWNER_ID'])

# === Local File Constants ===
INTERVAL_FILE = "interval.txt"
MESSAGES_FILE = "messages.txt"

# ===== Utility Functions =====
def get_interval():
    try:
        with open(INTERVAL_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 3600

def set_interval(seconds):
    with open(INTERVAL_FILE, "w") as f:
        f.write(str(seconds))

def get_messages():
    try:
        with open(MESSAGES_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["🕒 Default automated message."]

def save_messages(messages):
    with open(MESSAGES_FILE, "w") as f:
        for msg in messages:
            f.write(msg.strip() + "\n")

def add_message(new_msg):
    messages = get_messages()
    messages.append(new_msg)
    save_messages(messages)

def update_message(index, new_msg):
    messages = get_messages()
    if 0 <= index < len(messages):
        messages[index] = new_msg
        save_messages(messages)
        return True
    return False

def delete_message(index):
    messages = get_messages()
    if 0 <= index < len(messages):
        del messages[index]
        save_messages(messages)
        return True
    return False

# ===== Command Handlers =====
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

async def add_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addmessage <your message>")
        return

    new_msg = " ".join(context.args)
    add_message(new_msg)
    await update.message.reply_text("✅ Message added successfully!")

async def view_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    messages = get_messages()
    if not messages:
        await update.message.reply_text("⚠️ No messages found.")
        return

    formatted = "\n\n".join([f"{i + 1}. {msg}" for i, msg in enumerate(messages)])
    await update.message.reply_text(f"📋 Stored Messages:\n\n{formatted}")

async def edit_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /editmessage <index> <new message>")
        return

    try:
        index = int(context.args[0]) - 1
        new_msg = " ".join(context.args[1:])
        if update_message(index, new_msg):
            await update.message.reply_text("✅ Message updated successfully!")
        else:
            await update.message.reply_text("❌ Invalid index.")
    except ValueError:
        await update.message.reply_text("❌ Index must be a number.")

async def delete_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /deletemessage <index>")
        return

    try:
        index = int(context.args[0]) - 1
        if delete_message(index):
            await update.message.reply_text("✅ Message deleted successfully!")
        else:
            await update.message.reply_text("❌ Invalid index.")
    except ValueError:
        await update.message.reply_text("❌ Index must be a number.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"👋 Hey! Your Telegram user ID is: {user_id}")

# ===== Background Posting Task =====
async def post_loop(bot: Bot):
    last_post_time = datetime.min
    message_index = 0

    while True:
        interval = get_interval()
        now = datetime.now()
        elapsed = (now - last_post_time).total_seconds()

        if elapsed >= interval:
            messages = get_messages()
            if messages:
                await bot.send_message(chat_id=CHANNEL_ID, text=messages[message_index % len(messages)])
                message_index += 1
                last_post_time = now

        await asyncio.sleep(1)

# ===== Main Entrypoint =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setinterval", set_interval_command))
    app.add_handler(CommandHandler("addmessage", add_message_command))
    app.add_handler(CommandHandler("viewmessages", view_messages_command))
    app.add_handler(CommandHandler("editmessage", edit_message_command))
    app.add_handler(CommandHandler("deletemessage", delete_message_command))

    async def start_loop(application):
        asyncio.create_task(post_loop(application.bot))

    app.post_init = start_loop

    print("🚀 Bot is running...")
    app.run_polling()
