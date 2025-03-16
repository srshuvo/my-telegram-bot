import asyncio
import os
import json
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import Message
from fastapi import FastAPI

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI()

# ভিডিও ডাটা ফেচ করার ফাংশন
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
async def start(message: Message):
    await message.answer("👋 Welcome to Terabox Player Bot!\nSend me a Terabox URL to fetch the video.")

# URL হ্যান্ডলিং ফাংশন
@dp.message()
async def handle_url(message: Message):
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

# FastAPI Route for Render.com
@app.get("/")
def read_root():
    return {"status": "Bot is Running"}

# বট চালানোর ফাংশন
async def main():
    print("🤖 Bot is running...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# স্ক্রিপ্ট রান হলে asyncio দিয়ে চালু করা হবে
if __name__ == "__main__":
    asyncio.run(main())
