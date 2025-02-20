import asyncio
import os
import logging
import re

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

# -------------- আইডি এক্সট্রাকশন ও নতুন লিঙ্ক জেনারেশন ফাংশন --------------
def extract_id_from_xxxx_link(link: str) -> str:
    # নতুন লিঙ্ক ফরম্যাট থেকে ID বের করা (যেমন 123_abcXYZ)
    match = re.search(r"xxxx/s/([a-zA-Z0-9_]+)", link)
    if match:
        return match.group(1)
    return None

def generate_new_link_from_id(terabox_id: str) -> str:
    # নতুন লিঙ্ক তৈরি করা
    return f"https://mdiskplay.com/terabox/{terabox_id}"

def regenerate_id(original_id: str) -> str:
    # আইডির প্রথম অক্ষর বা সংখ্যা বাদ দেওয়া
    return original_id[1:] if len(original_id) > 1 else original_id

# -------------- /start কমান্ড হ্যান্ডলার --------------
@dp.message(F.text == "/start")
async def welcome_message(message: Message):
    first_name = message.from_user.first_name or "বন্ধু"
    welcome_text = (
        f"✨ স্বাগতম, {first_name}! 🌟\n"
        "আমাদের সেবায় আপনার আগমনকে স্বাগত জানাই! 💫\n\n"
        "🔗 যদি আপনি **xxxx** লিঙ্ক পাঠান, আমরা সেটি নিরাপদভাবে **PLAY** করে দিব। 🎥✨\n\n"
        "🤔 যেকোনো প্রশ্ন বা সহায়তার জন্য আমাদের সাথে যোগাযোগ করুন।\n\n"
        f"✨ Welcome, {first_name}! 🌟\n"
        "We're thrilled to have you here! 💫\n\n"
        "🔗 If you send a **xxxx** link, we'll safely **PLAY** it for you. 🎥✨\n\n"
        "🤔 If you have any questions or need assistance, feel free to ask! 😊"
    )
    try:
        await message.reply(welcome_text)
        # পিন করা বার্তা শুধুমাত্র /start কমান্ডে পিন হবে
        await pin_server_issue_message(message.chat.id)
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")

# -------------- পিন করা নোটিফিকেশন মেসেজ --------------
async def pin_server_issue_message(chat_id: int):
    message_text = (
        "⚠️ **সার্ভার সমস্যার কারণে বট এর লিঙ্ক পাঠাতে দেরি হতে পারে** ⚠️\n"
        "📌 **লিঙ্ক পাঠাতে থাকুন, সার্ভার ঠিক হলে সব ভিডিও পাঠানো হবে।**\n\n"
        "⚠️ **Due to server issues, the bot may take time to send links.** ⚠️\n"
        "📌 **Keep sending links, and once the server is fixed, all videos will be sent.**"
    )

    try:
        sent_message = await bot.send_message(chat_id, message_text, parse_mode="Markdown")
        await sent_message.pin()  # শুধুমাত্র /start কমান্ডে পিন হবে
    except Exception as e:
        logger.error(f"Error pinning message: {e}")

# -------------- মেসেজ হ্যান্ডলার: xxxx লিঙ্ক modify করা --------------
@dp.message()
async def modify_link(message: Message):
    text = message.text or message.caption
    if not text:
        return

    # xxxx লিঙ্ক থেকে আইডি এক্সট্রাক্ট করা
    xxxx_id = extract_id_from_xxxx_link(text)
    if not xxxx_id:
        return  # যদি সঠিক লিঙ্ক না হয় তবে কিছু না করা

    # নতুন লিঙ্ক তৈরি করা
    new_link = generate_new_link_from_id(xxxx_id)

    # টাইপিং ইফেক্ট দেখানোর জন্য
    await bot.send_chat_action(message.chat.id, action="typing")
    await asyncio.sleep(1.5)

    # কাস্টম বাটন সহ মেসেজ পাঠানো
    buttons = [
        [
            InlineKeyboardButton(
                text="🎬 Watch Video - Click to Watch!",  # কাস্টম বাটন টেক্সট
                url=new_link,  # নতুন লিঙ্ক
            ),
            InlineKeyboardButton(
                text="🔗 Share this Link Now!",  # শেয়ার লিঙ্ক বাটন টেক্সট
                switch_inline_query=new_link
            )
        ],
        [
            InlineKeyboardButton(
                text="♻️ Regenerate Link",  # রিজেনারেট বাটন টেক্সট
                callback_data=f"regenerate_link:{xxxx_id}"  # আইডি পাঠানো
            ),
            InlineKeyboardButton(
                text="🗑️ Delete This Message",  # কাস্টম ডিলিট বাটন টেক্সট
                callback_data="delete_message"
            )
        ]
    ]

    # কাস্টম স্টাইলিং সহ ইনলাইন কীবোর্ড তৈরি
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # শুধুমাত্র বাটন সহ মেসেজ পাঠানো
    sent_message = None
    if message.text:
        sent_message = await message.reply(text, reply_markup=keyboard)
    elif message.photo:
        sent_message = await message.reply_photo(photo=message.photo[-1].file_id, caption=text, reply_markup=keyboard)
    elif message.video:
        sent_message = await message.reply_video(video=message.video.file_id, caption=text, reply_markup=keyboard)
    elif message.document:
        sent_message = await message.reply_document(document=message.document.file_id, caption=text, reply_markup=keyboard)
    elif message.audio:
        sent_message = await message.reply_audio(audio=message.audio.file_id, caption=text, reply_markup=keyboard)
    elif message.voice:
        sent_message = await message.reply_voice(voice=message.voice.file_id, caption=text, reply_markup=keyboard)

# -------------- Regenerate Link Handler --------------
@dp.callback_query(F.data.startswith("regenerate_link:"))
async def regenerate_link(callback: CallbackQuery):
    try:
        # Callback data থেকে আইডি বের করা
        original_id = callback.data.split(":")[1]
        
        # আইডি রিজেনারেট করা
        regenerated_id = regenerate_id(original_id)
        
        # নতুন লিঙ্ক তৈরি করা
        new_link = generate_new_link_from_id(regenerated_id)
        
        # নতুন লিঙ্ক সহ মেসেজ আপডেট করা
        await callback.message.edit_text(
            f"🎬 New Video Link: {new_link}\n\n"
            "🔗 Share this Link Now! 📲\n\n"
            "♻️ Click the Regenerate button if you want another link.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🎬 Watch Video", url=new_link)],
                [InlineKeyboardButton("🔗 Share this Link Now", switch_inline_query=new_link)],
                [InlineKeyboardButton("♻️ Regenerate Link", callback_data=f"regenerate_link:{regenerated_id}")],
                [InlineKeyboardButton("🗑️ Delete This Message", callback_data="delete_message")]
            ])
        )
        await callback.answer("✅ New link generated successfully!")
    except Exception as e:
        logger.error(f"Error regenerating link: {e}")
        await callback.answer("❌ Failed to regenerate link.", show_alert=True)

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
    port = int(os.getenv("PORT", 8080))  # Render স্বয়ংক্রিয়ভাবে পোর্টটি প্রদান করে
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ Webserver is running on port {port}")

# -------------- Main ফাংশন: Webhook মুছে ফেলুন এবং Polling শুরু করুন --------------
async def main():
    # Webhook মুছে ফেলুন
    await bot.delete_webhook()

    logger.info("✅ Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
