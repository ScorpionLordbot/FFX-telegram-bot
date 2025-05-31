import os
import asyncio
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Environment Variables ===
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
OWNER_ID = int(os.environ['OWNER_ID'])

# === File Constants ===
MESSAGES_FILE = "messages.txt"  # Each line: interval|message

# ===== Utility Functions =====

def load_messages():
    messages = []
    try:
        with open(MESSAGES_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    interval = int(parts[0])
                    message = parts[1]
                    messages.append((interval, message))
    except:
        pass
    return messages

def save_messages(messages):
    with open(MESSAGES_FILE, "w") as f:
        for interval, msg in messages:
            f.write(f"{interval}|{msg}\n")

# ===== Command Handlers =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"👋 Hey! Your Telegram user ID is: {user_id}")

async def add_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addmessage <interval_in_seconds> <your message>")
        return

    try:
        interval = int(context.args[0])
        msg = " ".join(context.args[1:])
        messages = load_messages()
        messages.append((interval, msg))
        save_messages(messages)
        await update.message.reply_text("✅ Message added successfully.")
    except ValueError:
        await update.message.reply_text("❌ Invalid interval. It should be a number.")

async def view_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    messages = load_messages()
    if not messages:
        await update.message.reply_text("ℹ️ No messages stored.")
        return

    reply = "📋 Stored Messages:\n\n"
    for idx, (interval, msg) in enumerate(messages, start=1):
        reply += f"{idx}. ({interval}s) {msg}\n"
    await update.message.reply_text(reply)

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
        messages = load_messages()
        if 0 <= index < len(messages):
            interval = messages[index][0]
            messages[index] = (interval, new_msg)
            save_messages(messages)
            await update.message.reply_text("✏️ Message updated.")
        else:
            await update.message.reply_text("❌ Invalid message index.")
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid index.")

async def delete_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /deletemessage <index>")
        return

    try:
        index = int(context.args[0]) - 1
        messages = load_messages()
        if 0 <= index < len(messages):
            messages.pop(index)
            save_messages(messages)
            await update.message.reply_text("🗑️ Message deleted.")
        else:
            await update.message.reply_text("❌ Invalid message index.")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")

# ===== Background Posting Task =====

async def post_loop(bot: Bot):
    messages = load_messages()
    if not messages:
        return

    index = 0
    while True:
        messages = load_messages()
        if not messages:
            await asyncio.sleep(10)
            continue

        interval, message = messages[index % len(messages)]
        await bot.send_message(chat_id=CHANNEL_ID, text=message)
        await asyncio.sleep(interval)
        index += 1

# ===== Main Entrypoint =====

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmessage", add_message_command))
    app.add_handler(CommandHandler("viewmessages", view_messages_command))
    app.add_handler(CommandHandler("editmessage", edit_message_command))
    app.add_handler(CommandHandler("deletemessage", delete_message_command))

    async def start_loop(application):
        asyncio.create_task(post_loop(application.bot))

    app.post_init = start_loop

    print("🚀 Bot is running...")
    app.run_polling()
