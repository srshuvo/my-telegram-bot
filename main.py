import os
import re
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
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

# -------------- TERA BOX লিঙ্ক থেকে আইডি এক্সট্রাকশন --------------
def extract_id_from_terabox_link(text: str) -> str:
    match = re.search(r"terabox.com/s/([a-zA-Z0-9_]+)", text)
    if match:
        return match.group(1)
    return None

# -------------- নতুন লিঙ্ক তৈরি --------------
def generate_new_link_from_id(id: str) -> str:
    return f"https://mdiskplay.com/terabox/{id}"

# -------------- /start কমান্ড হ্যান্ডলার --------------
@dp.message(Command("start"))
async def welcome_message(message: Message):
    first_name = message.from_user.first_name or "বন্ধু"
    welcome_text = (
        f"✨ স্বাগতম, {first_name}! 🌟\n"
        "আমাদের সেবায় আপনার আগমনকে স্বাগত জানাই! 💫\n\n"
        "🔗 যদি আপনি **TERA BOX** লিঙ্ক পাঠান, আমরা সেটি নিরাপদভাবে **PLAY** করে দিব। 🎥✨\n\n"
        "🤔 যেকোনো প্রশ্ন বা সহায়তার জন্য আমাদের সাথে যোগাযোগ করুন।\n\n"
        f"✨ Welcome, {first_name}! 🌟\n"
        "We're thrilled to have you here! 💫\n\n"
        "🔗 If you send a **TERA BOX** link, we'll safely **PLAY** it for you. 🎥✨\n\n"
        "🤔 If you have any questions or need assistance, feel free to ask! 😊"
    )
    try:
        await message.reply(welcome_text)
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")

# -------------- TERA BOX লিঙ্ক modify করা --------------
@dp.message()
async def modify_link(message: Message):
    text = message.text or message.caption
    if not text:
        return

    # TERA BOX লিঙ্ক থেকে আইডি বের করা
    extracted_id = extract_id_from_terabox_link(text)
    if not extracted_id:
        return

    # নতুন লিঙ্ক তৈরি করা
    new_link = generate_new_link_from_id(extracted_id)

    # ইনলাইন বাটন সহ মেসেজ তৈরি করা
    buttons = [
        [InlineKeyboardButton(text="🎬 Watch Video", url=new_link)],
        [InlineKeyboardButton(text="🔗 Share this Link Now!", switch_inline_query=new_link)],
        [InlineKeyboardButton(text="♻️ Regenerate", callback_data=f"regenerate_{extracted_id}")],
        [InlineKeyboardButton(text="❌ Delete", callback_data="delete_message")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # মেসেজ পাঠানো
    await message.reply(text=f"Here is your TERA BOX link: {new_link}", reply_markup=keyboard)

# -------------- Regenerate Button Handler --------------
@dp.callback_query(lambda c: c.data and c.data.startswith("regenerate_"))
async def regenerate_link(callback: CallbackQuery):
    extracted_id = callback.data.split("_")[1]
    new_id = extracted_id[1:]  # প্রথম অক্ষর/সংখ্যা বাদ দেয়া
    new_link = generate_new_link_from_id(new_id)
    
    await callback.message.edit_text(f"Here is your regenerated link: {new_link}")
    await callback.answer(f"✅ New ID generated: {new_id}", show_alert=True)

# -------------- Delete Button Handler --------------
@dp.callback_query(lambda c: c.data == "delete_message")
async def delete_message(callback: CallbackQuery):
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await callback.answer("✅ Message deleted successfully!", show_alert=True)
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        await callback.answer("❌ Failed to delete message!", show_alert=True)

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
