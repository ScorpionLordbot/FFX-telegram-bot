import os
import asyncio
from telegram import Bot
from datetime import datetime

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

bot = Bot(token=BOT_TOKEN)

async def post():
    while True:
        message = f"🚀 Hello from Railway!\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await bot.send_message(chat_id=CHANNEL_ID, text=message)
        await asyncio.sleep(3600)  # every hour

asyncio.run(post())
