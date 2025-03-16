import logging
import os
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils.executor import start_webhook

from dotenv import load_dotenv

# .env ফাইল থেকে টোকেন এবং ওয়েবহুক ইউআরএল লোড করুন
load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Bot এবং Dispatcher তৈরি
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Flask অ্যাপ সেট আপ
app = Flask(__name__)

# লগিং কনফিগারেশন
logging.basicConfig(level=logging.INFO)

# /start কমান্ড হ্যান্ডলার
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("হ্যালো! আমি আপনার সহকারী।")

# Webhook হ্যান্ডলার
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    try:
        # Aiogram 3.x তে from_json() ব্যবহার করুন
        update = types.Update.from_json(json_str)
        dp.process_update(update)
        return "OK"
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        return "Error", 500

# Webhook সেটআপের জন্য ফাংশন
async def on_start():
    # ওয়েবহুক সেট করুন
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to: {WEBHOOK_URL}")

# Flask এ ওয়েবহুক চালু করার জন্য
@app.before_first_request
def before_first_request():
    loop = asyncio.get_event_loop()
    loop.create_task(on_start())

# Flask অ্যাপ চালু করুন
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
