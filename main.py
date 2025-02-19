import re
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# -------------- Logging সেটআপ --------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------- Environment Variable থেকে BOT_TOKEN নেওয়া --------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# -------------- Bot এবং Dispatcher Initialization --------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# -------------- URL Extract ও Modify করার ফাংশন --------------
def extract_modified_urls(text: str) -> list:
    urls = re.findall(r"https?://[^\s]+", text)
    unique_urls = set()
    modified_urls = []
    for url in urls:
        if "tera" in url and not url.startswith("https://player.terabox.tech/?url="):
            modified_url = f"https://player.terabox.tech/?url={url}"
            if modified_url not in unique_urls:
                unique_urls.add(modified_url)
                modified_urls.append(modified_url)
    return modified_urls

# -------------- /start কমান্ড হ্যান্ডলার --------------
@dp.message(F.text == "/start")
async def welcome_message(message: Message):
    first_name = message.from_user.first_name or "বন্ধু"
    welcome_text = (
        f"✨ স্বাগতম, {first_name}! 🌟\n"
        "🔗 আপনি যদি **TERA BOX** লিঙ্ক পাঠান, আমরা সেটি **PLAY** করে দিব। 🎥✨\n"
    )
    try:
        await message.reply(welcome_text)
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")

# -------------- মেসেজ হ্যান্ডলার: TERA BOX লিঙ্ক modify করা --------------
@dp.message()
async def modify_link(message: Message):
    text = message.text or message.caption
    if not text:
        return

    modified_urls = extract_modified_urls(text)
    if not modified_urls:
        return

    # টাইপিং ইফেক্ট দেখানোর জন্য
    await bot.send_chat_action(message.chat.id, action="typing")
    await asyncio.sleep(1.5)

    # ইনলাইন কীবোর্ড তৈরি
    buttons = [
        [InlineKeyboardButton(text=f"🎬 Watch Video {i+1}", url=url)]
        for i, url in enumerate(modified_urls)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # মেসেজ পাঠানো
    await message.reply("✅ আপনার ভিডিও লিঙ্ক রেডি:", reply_markup=keyboard)

# -------------- Keep-Alive ওয়েব সার্ভার (aiohttp) --------------
async def handle(request):
    return web.Response(text="I'm alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("✅ Webserver is running on port 8080")

# -------------- Main ফাংশন --------------
async def main():
    asyncio.create_task(start_webserver())
    logger.info("✅ Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
