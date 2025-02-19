import os
import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# -------------- Logging সেটআপ --------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------- Environment Variable থেকে BOT_TOKEN নেওয়া --------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render থেকে BOT_TOKEN environment variable এ থেকে টোকেন নেয়া
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
        if "tera" in url:  # "tera" শব্দ থাকলে id বের করা
            # URL থেকে ID বের করা, এখানে শুধু 'url' এর পরের অংশ থেকে ID ধরে রাখা
            id_match = re.search(r"(https?://[^\s]+)", url)
            if id_match:
                id = id_match.group(1)  # URL থেকে ID সংগ্রহ করা
                # নতুন লিঙ্ক তৈরি
                modified_url = f"https://mdiskplay.com/terabox/{id}"
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

    # মূল লিঙ্কগুলি মুছে ফেলা
    for url in modified_urls:
        text = text.replace(url, "")

    # প্রতিটি modified URL এর জন্য ইনলাইন বাটন তৈরি
    buttons = []
    for i, url in enumerate(modified_urls):
        buttons.append([ 
            InlineKeyboardButton(
                text=f"🎬 Watch Video {i+1} - Click to Watch!",  
                url=url,
            ),
            InlineKeyboardButton(
                text="🔗 Share this Link Now!",  
                switch_inline_query=url
            ),
            InlineKeyboardButton(
                text="🔄 Regenerate",  
                callback_data=f"regenerate_{url}"  # Regenerate বাটনের জন্য callback_data
            )
        ])
    buttons.append([ 
        InlineKeyboardButton(
            text="🗑️ Delete This Message", 
            callback_data="delete_message"
        )
    ])

    # কাস্টম স্টাইলিং সহ ইনলাইন কীবোর্ড তৈরি
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # শুধুমাত্র বাটন সহ মেসেজ পাঠানো
    sent_message = await message.reply(text, reply_markup=keyboard)

# -------------- Regenerate Button Handler --------------
@dp.callback_query(F.data.startswith("regenerate_"))
async def regenerate_link(callback: CallbackQuery):
    url = callback.data.split("_", 1)[1]  # URL এর id এর অংশ আলাদা করা
    new_id = url[1:]  # প্রথম অক্ষর কেটে ফেলা
    new_url = f"https://mdiskplay.com/terabox/{new_id}"  # নতুন লিঙ্ক তৈরি

    # Regenerated লিঙ্ক সহ নতুন মেসেজ পাঠানো
    await callback.message.edit_text(
        f"🔄 **Regenerated Link:**\n\n{new_url}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[ 
                [InlineKeyboardButton(text="🎬 Watch Video - Click to Watch!", url=new_url)],
                [InlineKeyboardButton(text="🔗 Share this Link Now!", switch_inline_query=new_url)]
            ]
        )
    )
    await callback.answer()  # Callback Answer

# -------------- Delete Button Handler --------------
@dp.callback_query(F.data == "delete_message")
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
    app.router.add_post(f'/{BOT_TOKEN}', handle)  # Webhook URL হবে এই রকম
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("✅ Webserver is running on port 8080")

# -------------- Main ফাংশন: ওয়েব সার্ভার ও বটের পোলিং শুরু করা --------------
async def main():
    asyncio.create_task(start_webserver())
    logger.info("✅ Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
