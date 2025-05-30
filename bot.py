import asyncio
from telegram import Bot
from datetime import datetime

BOT_TOKEN = '8018996550:AAECewNhwNkW0ue2sx0CKeTUc4QN3nYq7cg'
CHANNEL_USERNAME = '@deadlysync100'

bot = Bot(token=BOT_TOKEN)

async def post_regularly():
    while True:
        message = f"📢 Hello from PythonAnywhere!\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await bot.send_message(chat_id=CHANNEL_USERNAME, text=message)
        await asyncio.sleep(3600)  # Every hour

async def main():
    print("Bot started...")
    await post_regularly()

asyncio.run(main())
