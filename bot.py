import os
import asyncio
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncpg

# === Environment Variables ===
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
OWNER_ID = int(os.environ['OWNER_ID'])
DATABASE_URL = os.environ['DATABASE_URL']

# ===== Database Utility =====

async def get_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

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
        async with context.application.bot_data['db'].acquire() as conn:
            await conn.execute("INSERT INTO messages (text, interval) VALUES ($1, $2)", text, interval)
        await update.message.reply_text("✅ Message added!")
    except ValueError:
        await update.message.reply_text("❌ Invalid interval. Use a number in seconds.")

async def view_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    async with context.application.bot_data['db'].acquire() as conn:
        rows = await conn.fetch("SELECT id, text, interval FROM messages ORDER BY id")

    if not rows:
        await update.message.reply_text("📭 No messages stored.")
        return

    reply = "📋 Stored Messages:\n"
    for row in rows:
        reply += f"{row['id']}. ⏱ {row['interval']}s — {row['text']}\n"
    await update.message.reply_text(reply)

async def edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /editmessage <id> <new message>")
        return

    try:
        msg_id = int(context.args[0])
        new_text = " ".join(context.args[1:])
        async with context.application.bot_data['db'].acquire() as conn:
            result = await conn.execute("UPDATE messages SET text = $1 WHERE id = $2", new_text, msg_id)
        if result == "UPDATE 1":
            await update.message.reply_text("✏️ Message updated.")
        else:
            await update.message.reply_text("❌ Message not found.")
    except ValueError:
        await update.message.reply_text("❌ ID must be a number.")

async def edit_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /editinterval <id> <new interval>")
        return

    try:
        msg_id = int(context.args[0])
        new_interval = int(context.args[1])
        async with context.application.bot_data['db'].acquire() as conn:
            result = await conn.execute("UPDATE messages SET interval = $1 WHERE id = $2", new_interval, msg_id)
        if result == "UPDATE 1":
            await update.message.reply_text("⏱ Interval updated.")
        else:
            await update.message.reply_text("❌ Message not found.")
    except ValueError:
        await update.message.reply_text("❌ Invalid input. ID and interval must be numbers.")

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /deletemessage <id>")
        return

    try:
        msg_id = int(context.args[0])
        async with context.application.bot_data['db'].acquire() as conn:
            result = await conn.execute("DELETE FROM messages WHERE id = $1", msg_id)
        if result == "DELETE 1":
            await update.message.reply_text("🗑 Message deleted.")
        else:
            await update.message.reply_text("❌ Message not found.")
    except ValueError:
        await update.message.reply_text("❌ ID must be a number.")

# ===== Background Posting Loop =====

async def post_loop(bot: Bot, db_pool):
    while True:
        async with db_pool.acquire() as conn:
            messages = await conn.fetch("SELECT id, text, interval FROM messages ORDER BY id")

        if not messages:
            await asyncio.sleep(10)
            continue

        for msg in messages:
            await bot.send_message(chat_id=CHANNEL_ID, text=msg['text'])
            await asyncio.sleep(msg['interval'])

# ===== Main Entrypoint =====

if __name__ == "__main__":
    async def main():
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Connect to PostgreSQL
        db_pool = await get_db_pool()
        app.bot_data['db'] = db_pool

        # Command Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("addmessage", add_message))
        app.add_handler(CommandHandler("viewmessages", view_messages))
        app.add_handler(CommandHandler("editmessage", edit_message))
        app.add_handler(CommandHandler("editinterval", edit_interval))
        app.add_handler(CommandHandler("deletemessage", delete_message))

        # Background loop
        async def start_loop(app):
            asyncio.create_task(post_loop(app.bot, db_pool))

        app.post_init = start_loop
        print("🚀 Bot is running...")
        await app.run_polling()

    asyncio.run(main())
