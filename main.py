import os
import re
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from flask import Flask, request
from threading import Thread

# ✅ Environment Variables থেকে Bot Token নেওয়া
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ Bot & Dispatcher সেটআপ (aiogram 3.x অনুযায়ী)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✅ Regex ফাংশন: Terabox লিংক থেকে ID বের করা
def extract_terabox_id(url):
    match = re.search(r"(?:id=|s/)([\w\d]+)", url)
    return match.group(1) if match else None

# ✅ API ফাংশন: Terabox API থেকে ভিডিওর তথ্য পাওয়া
def fetch_video_data(terabox_id):
    api_url = f"https://www.terabox.tech/api/yttera?id={terabox_id}"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return data.get("response", [])[0]  # প্রথম ভিডিওর তথ্য
        except ValueError:
            return None
    return None

# ✅ /start কমান্ড
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("👋 Welcome to *Terabox Player Bot*! Send me a Terabox URL to fetch the video.", parse_mode="Markdown")

# ✅ লিংক প্রসেস করা
@dp.message()
async def process_link(message: types.Message):
    url = message.text.strip()
    terabox_id = extract_terabox_id(url)

    if not terabox_id:
        await message.answer("❌ Invalid Terabox URL! Please send a valid link.")
        return

    video_data = fetch_video_data(terabox_id)

    if not video_data:
        await message.answer("❌ Couldn't fetch video details. Try again later.")
        return

    # ✅ ভিডিওর তথ্য সংগ্রহ
    title = video_data["title"]
    thumbnail = video_data["thumbnail"]
    fast_download = video_data["resolutions"].get("Fast Download", "#")
    hd_download = video_data["resolutions"].get("HD Video", "#")

    # ✅ Inline Keyboard Buttons
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Fast Download", url=fast_download)],
        [InlineKeyboardButton(text="🔼 HD Download", url=hd_download)]
    ])

    # ✅ ইউজারকে মেসেজ পাঠানো
    await message.answer_photo(
        photo=thumbnail,
        caption=f"🎬 *{title}*\n\n🔗 [Watch Video](https://apis.forn.fun/tera/data.php?id={terabox_id})",
        parse_mode="Markdown",
        reply_markup=buttons
    )

# ✅ Flask Webhook (Render-এর জন্য)
app = Flask(__name__)

@app.route('/')
def index():
    return "Terabox Bot is Running!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = await request.get_json()
    await dp.feed_update(bot, types.Update(**update))
    return "OK"

# ✅ Flask সার্ভার চালু করা
def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ✅ বট চালু করা (Polling Mode)
async def run_bot():
    await dp.start_polling(bot)

# ✅ Flask & Bot একসাথে চালানো
if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(run_bot())
