import re
import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
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

# -------------- TERA BOX লিংক থেকে আইডি বের করা --------------
def extract_id_from_terabox_link(link: str) -> str:
    match = re.search(r"https?://[^/]+/s/([^?&]+)", link)
    return match.group(1) if match else None

# -------------- নতুন লিংক তৈরি করা --------------
def generate_new_link_from_id(file_id: str) -> str:
    return f"https://mdiskplay.com/terabox/{file_id}"

# -------------- /start কমান্ড হ্যান্ডলার --------------
@dp.message(Command("start"))
async def welcome_message(message: Message):
    first_name = message.from_user.first_name or "বন্ধু"
    welcome_text = (
        f"✨ স্বাগতম, {first_name}! 🌟\n"
        "আমাদের সেবায় আপনার আগমনকে স্বাগত জানাই! 💫\n\n"
        "🔗 যদি আপনি **TERA BOX** লিঙ্ক পাঠান, আমরা সেটি পরিবর্তন করে নতুন লিংক প্রদান করব। 🎥✨\n\n"
        "🤔 যেকোনো প্রশ্ন বা সহায়তার জন্য আমাদের সাথে যোগাযোগ করুন। 😊"
    )
    await message.reply(welcome_text)

# -------------- মেসেজ হ্যান্ডলার: TERA BOX লিঙ্ক modify করা --------------
@dp.message()
async def modify_link(message: Message):
    text = message.text or message.caption
    if not text:
        return

    urls = re.findall(r"https?://[^\s]+", text)  # সব লিংক খুঁজে বের করা
    unique_links = {}  # ডুপ্লিকেট রোধ করতে

    for url in urls:
        if "tera" in url:  # শুধুমাত্র TERA BOX লিংক পরিবর্তন করবে
            file_id = extract_id_from_terabox_link(url)
            if file_id and file_id not in unique_links:
                unique_links[file_id] = generate_new_link_from_id(file_id)

    if not unique_links:
        return  # যদি কোনো TERA BOX লিংক না থাকে, তাহলে কিছু করবে না

    # টাইপিং ইফেক্ট দেখানোর জন্য
    await bot.send_chat_action(message.chat.id, action="typing")
    await asyncio.sleep(1.5)

    # বাটন তৈরি
    buttons = []
    for file_id, new_url in unique_links.items():
        buttons.append([
            InlineKeyboardButton(text="🎬 ভিডিও দেখুন", url=new_url),
            InlineKeyboardButton(text="🔗 শেয়ার করুন", switch_inline_query=new_url),
            InlineKeyboardButton(text="♻️ রিজেনারেট", callback_data=f"regenerate_{file_id}")
        ])
    
    buttons.append([
        InlineKeyboardButton(text="❌ ডিলিট", callback_data="delete_message")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # মেসেজ পাঠানো
    sent_message = await message.reply("🔗 আপনার লিংক পরিবর্তন করা হয়েছে!", reply_markup=keyboard)

# -------------- রিজেনারেট বাটন হ্যান্ডলার --------------
@dp.callback_query(lambda c: c.data.startswith("regenerate_"))
async def regenerate_link(callback: CallbackQuery):
    file_id = callback.data.replace("regenerate_", "")
    new_id = file_id[1:]  # প্রথম ক্যারেক্টার বাদ দিয়ে নতুন আইডি তৈরি
    new_url = generate_new_link_from_id(new_id)

    buttons = [
        [InlineKeyboardButton(text="🎬 নতুন ভিডিও দেখুন", url=new_url)],
        [InlineKeyboardButton(text="🔗 শেয়ার করুন", switch_inline_query=new_url)],
        [InlineKeyboardButton(text="♻️ আবার রিজেনারেট", callback_data=f"regenerate_{new_id}")],
        [InlineKeyboardButton(text="❌ ডিলিট", callback_data="delete_message")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("✅ নতুন লিংক তৈরি হয়েছে!")

# -------------- Delete Button Handler --------------
@dp.callback_query(lambda c: c.data == "delete_message")
async def delete_message(callback: CallbackQuery):
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await callback.answer("✅ মেসেজ মুছে ফেলা হয়েছে!", show_alert=True)
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        await callback.answer("❌ মেসেজ ডিলিট করতে ব্যর্থ!", show_alert=True)

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

# -------------- Main ফাংশন: ওয়েব সার্ভার ও বটের পোলিং শুরু করা --------------
async def main():
    asyncio.create_task(start_webserver())
    logger.info("✅ Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
