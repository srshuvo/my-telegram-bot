import os
import asyncio
import json
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from fastapi import FastAPI
from flask import Flask

# .env ফাইল থেকে Environment Variables লোড করা
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Flask & FastAPI Instance (Render.com-এ হোস্টিংয়ের জন্য)
flask_app = Flask(__name__)
fastapi_app = FastAPI()

# Aiogram Bot Setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Terabox ভিডিও ডাটা ফেচ করার ফাংশন
def fetch_video_data(url):
    try:
        id = url.split("/")[-1]  # URL থেকে ID বের করা
        api_url = f"https://wholly-api.skinnyrunner.com/get/website-data.php?get_html=https://www.terabox.tech/api/yttera?id={id}"
        response = requests.get(api_url)
        data = json.loads(response.text)

        if "response" not in data:
            return None

        video_data = data["response"][0]
        return {
            "title": video_data["title"],
            "thumbnail": video_data["thumbnail"],
            "fast_download": video_data["resolutions"]["Fast Download"],
            "hd_download": video_data["resolutions"]["HD Video"],
            "video_url": f"https://apis.forn.fun/tera/data.php?id={id}"
        }
    except:
        return None

# Start Command
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 Welcome to Terabox Player Bot!\nSend me a Terabox URL to fetch the video.")

# URL হ্যান্ডলিং ফাংশন
@dp.message()
async def handle_url(message: types.Message):
    url = message.text.strip()
    
    if "terabox" not in url:
        await message.answer("❌ Invalid Terabox URL! Please send a valid link.")
        return

    video_data = fetch_video_data(url)

    if not video_data:
        await message.answer("⚠️ Failed to fetch video data. Please try again later.")
        return

    # ইনলাইন বোতাম তৈরি
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Fast Download", url=video_data["fast_download"])],
        [InlineKeyboardButton(text="🔼 HD Download", url=video_data["hd_download"])]
    ])

    # ভিডিও Thumbnail সহ মেসেজ পাঠানো
    await message.answer_photo(
        photo=video_data["thumbnail"],
        caption=f"🎬 *{video_data['title']}*\n\n🔗 [Watch Video]({video_data['video_url']})",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# FastAPI Route for Render.com (Status Check)
@fastapi_app.get("/")
def read_root():
    return {"status": "Bot is Running"}

# Flask Route for Render.com (Alternative)
@flask_app.route("/")
def home():
    return "Bot is Running Successfully!"

# বট চালানোর ফাংশন
async def main():
    print("🤖 Bot is running...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# স্ক্রিপ্ট রান হলে asyncio দিয়ে চালু করা হবে
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())

    # Flask এবং FastAPI একসাথে চালানো
    import threading
    threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=8000)).start()
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)
