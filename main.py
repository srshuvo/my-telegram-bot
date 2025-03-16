import os
import json
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from fastapi import FastAPI

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # এখানে আপনার Bot Token বসান
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

app = FastAPI()  # Render.com-এ হোস্টিংয়ের জন্য FastAPI ব্যবহার করা হবে

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
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("👋 Welcome to Terabox Player Bot!\nSend me a Terabox URL to fetch the video.")

# URL হ্যান্ডলিং ফাংশন
@dp.message_handler()
async def handle_url(message: types.Message):
    url = message.text.strip()
    
    if "terabox" not in url:
        await message.reply("❌ Invalid Terabox URL! Please send a valid link.")
        return

    video_data = fetch_video_data(url)

    if not video_data:
        await message.reply("⚠️ Failed to fetch video data. Please try again later.")
        return

    # ইনলাইন বোতাম তৈরি
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📥 Fast Download", url=video_data["fast_download"]),
        InlineKeyboardButton("🔼 HD Download", url=video_data["hd_download"])
    )

    # ভিডিও Thumbnail সহ মেসেজ পাঠানো
    await message.reply_photo(
        photo=video_data["thumbnail"],
        caption=f"🎬 *{video_data['title']}*\n\n🔗 [Watch Video]({video_data['video_url']})",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Render.com-এর জন্য FastAPI Route
@app.get("/")
def read_root():
    return {"status": "Bot is Running"}

# বট চালানো
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
