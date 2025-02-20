import re
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os

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

# -------------- TERA BOX লিঙ্ক থেকে আইডি এক্সট্রাক্ট করার ফাংশন --------------
def extract_id_from_terabox_link(link: str) -> str:
    """
    TERA BOX লিঙ্ক থেকে ID বের করার ফাংশন।
    উদাহরণ: https://www.terabox.com/s/123_abcXYZ -> 123_abcXYZ
    """
    match = re.search(r"terabox.com/s/([a-zA-Z0-9_]+)", link)
    if match:
        return match.group(1)
    return None

# -------------- আইডি থেকে নতুন লিঙ্ক তৈরি করার ফাংশন --------------
def generate_new_link_from_id(terabox_id: str) -> str:
    """
    আইডি ব্যবহার করে নতুন লিঙ্ক তৈরি করার ফাংশন।
    উদাহরণ: 123_abcXYZ -> https://mdiskplay.com/terabox/123_abcXYZ
    """
    return f"https://mdiskplay.com/terabox/{terabox_id}"

# -------------- আইডি রিজেনারেট করার ফাংশন --------------
def regenerate_id(terabox_id: str) -> str:
    """
    আইডি থেকে প্রথম অক্ষর বা সংখ্যা বাদ দিয়ে নতুন আইডি তৈরি করার ফাংশন।
    উদাহরণ: 123_abcXYZ -> 23_abcXYZ
    """
    return terabox_id[1:]

# -------------- TERA শব্দটি খুঁজে বের করে লিঙ্ক পরিবর্তন করার ফাংশন --------------
def modify_terabox_links(text: str) -> str:
    """
    পাঠানো টেক্সটের মধ্যে যেসব TERA BOX লিঙ্ক আছে, সেগুলোর আইডি বের করে নতুন লিঙ্ক তৈরি করবে।
    TERA শব্দটি লিঙ্কে খুঁজে বের করে পরিবর্তন করবে।
    """
    # সব TERA শব্দযুক্ত লিঙ্ক খুঁজে বের করা
    urls = re.findall(r"https?://[^\s]+tera[^\s]*", text)
    
    # প্রতিটি লিঙ্কের জন্য আইডি বের করা এবং নতুন লিঙ্ক তৈরি করা
    for url in urls:
        terabox_id = extract_id_from_terabox_link(url)
        if terabox_id:
            new_link = generate_new_link_from_id(terabox_id)
            # পুরানো লিঙ্কটি নতুন লিঙ্ক দিয়ে পরিবর্তন করা
            text = text.replace(url, new_link)
    
    return text

# -------------- /start কমান্ড হ্যান্ডলার --------------
@dp.message(commands=["start"])
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

    # TERA BOX লিঙ্কগুলি modify করা
    modified_text = modify_terabox_links(text)

    # টাইপিং ইফেক্ট দেখানোর জন্য
    await bot.send_chat_action(message.chat.id, action="typing")

    # ইনলাইন বাটন সহ মেসেজ পাঠানো
    buttons = [
        [
            InlineKeyboardButton(
                text="🎬 Watch Video",  # কাস্টম বাটন টেক্সট
                url="https://www.example.com",  # এখানে আপনার ভিডিও লিঙ্ক দিন
            ),
            InlineKeyboardButton(
                text="🔗 Share this Link Now!",  # শেয়ার লিঙ্ক বাটন টেক্সট
                switch_inline_query=modified_text,
            ),
            InlineKeyboardButton(
                text="♻️ Regenerate",  # রিজেনারেট বাটন
                callback_data=f"regenerate_{text}",  # রিজেনারেটের জন্য CallbackData
            ),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(modified_text, reply_markup=keyboard)

# -------------- Regenerate Button Handler --------------
@dp.callback_query()
async def regenerate(callback: CallbackQuery):
    try:
        # callback_data থেকে আইডি পাওয়া
        action, original_id = callback.data.split("_", 1)
        
        if action == "regenerate":
            # নতুন আইডি তৈরি করা
            new_id = regenerate_id(original_id)
            new_link = generate_new_link_from_id(new_id)

            # নতুন লিঙ্ক এবং আইডি সহ মেসেজ আপডেট করা
            await callback.message.edit_text(
                f"🎬 New Video Link: {new_link}\n\n"
                "🔗 Share this link or click below to regenerate another one.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("♻️ Regenerate Again", callback_data=f"regenerate_{new_id}")
                )
            )

            await callback.answer("✅ New link generated successfully!", show_alert=True)
    except Exception as e:
        logger.error(f"Error in regenerate callback: {e}")
        await callback.answer("❌ Failed to regenerate link.", show_alert=True)

# -------------- Main ফাংশন: বটের পোলিং শুরু করা --------------
async def main():
    logger.info("✅ Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
