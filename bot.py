import os
import asyncio
import json
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Environment Variables ===
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
OWNER_ID = int(os.environ['OWNER_ID'])

# === File Constants ===
MESSAGE_FILE = "messages.json"

# ===== Utility Functions =====

# Load messages from file (list of dicts)
def load_messages():
    if not os.path.exists(MESSAGE_FILE):
        return []
    with open(MESSAGE_FILE, "r") as f:
        return json.load(f)

# Save messages to file
def save_messages(messages):
    with open(MESSAGE_FILE, "w") as f:
        json.dump(messages, f, indent=2)

# ===== Command Handlers =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"👋 Hey! Your Telegram user ID is: {user_id}")

async def add_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addmessage <interval> <message>")
        return

    try:
        interval = int(context.args[0])
        text = " ".join(context.args[1:])
        messages = load_messages()
        messages.append({"interval": interval, "text": text})
        save_messages(messages)
        await update.message.reply_text("✅ Message added!")
    except ValueError:
        await update.message.reply_text("❌ Invalid interval. Use a number in seconds.")

async def view_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    messages = load_messages()
    if not messages:
        await update.message.reply_text("📭 No messages stored.")
        return

    reply = "📋 Stored Messages:\n"
    for idx, msg in enumerate(messages):
        reply += f"{idx + 1}. ⏱ {msg['interval']}s — {msg['text']}\n"
    await update.message.reply_text(reply)

async def edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /editmessage <index> <new message>")
        return

    try:
        idx = int(context.args[0]) - 1
        new_text = " ".join(context.args[1:])
        messages = load_messages()
        if idx < 0 or idx >= len(messages):
            await update.message.reply_text("❌ Invalid index.")
            return
        messages[idx]['text'] = new_text
        save_messages(messages)
        await update.message.reply_text("✏️ Message updated.")
    except ValueError:
        await update.message.reply_text("❌ Index must be a number.")

async def edit_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /editinterval <index> <new interval>")
        return

    try:
        idx = int(context.args[0]) - 1
        new_interval = int(context.args[1])
        messages = load_messages()
        if idx < 0 or idx >= len(messages):
            await update.message.reply_text("❌ Invalid index.")
            return
        messages[idx]['interval'] = new_interval
        save_messages(messages)
        await update.message.reply_text("⏱ Interval updated.")
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Index and interval must be numbers.")

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /deletemessage <index>")
        return

    try:
        idx = int(context.args[0]) - 1
        messages = load_messages()
        if idx < 0 or idx >= len(messages):
            await update.message.reply_text("❌ Invalid index.")
            return
        removed = messages.pop(idx)
        save_messages(messages)
        await update.message.reply_text(f"🗑 Deleted message: {removed['text']}")
    except ValueError:
        await update.message.reply_text("❌ Index must be a number.")

# ===== Background Posting Loop =====

async def post_loop(bot: Bot):
    messages = load_messages()
    i = 0
    while True:
        if not messages:
            await asyncio.sleep(10)
            messages = load_messages()
            continue

        msg = messages[i % len(messages)]
        await bot.send_message(chat_id=CHANNEL_ID, text=msg['text'])
        await asyncio.sleep(msg['interval'])
        messages = load_messages()
        i += 1

# ===== Main Entrypoint =====

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmessage", add_message))
    app.add_handler(CommandHandler("viewmessages", view_messages))
    app.add_handler(CommandHandler("editmessage", edit_message))
    app.add_handler(CommandHandler("editinterval", edit_interval))
    app.add_handler(CommandHandler("deletemessage", delete_message))

    async def start_loop(application):
        asyncio.create_task(post_loop(application.bot))

    app.post_init = start_loop
    print("🚀 Bot is running...")
    app.run_polling()
