import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

# Environment variables লোড করা
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Bot & Dispatcher সেটআপ
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ID বের করা ও নতুন লিঙ্ক তৈরি করার ফাংশন
def extract_id_and_generate_link(url):
    match = re.search(r"tera(\w+)", url)
    if match:
        extracted_id = match.group(1)
        new_link = f"https://mdiskplay.com/terabox/{extracted_id}"
        return extracted_id, new_link
    return None, None

# ইনলাইন বোতাম তৈরি ফাংশন
def create_inline_buttons(link):
    buttons = InlineKeyboardMarkup(row_width=2)
    buttons.add(
        InlineKeyboardButton("🎬 Watch Video", url=link),
        InlineKeyboardButton("🔗 Share", switch_inline_query=link)
    )
    buttons.add(
        InlineKeyboardButton("🗑️ Delete", callback_data="delete"),
        InlineKeyboardButton("🔄 Regenerate", callback_data=f"regenerate:{link.split('/')[-1]}")
    )
    return buttons

# মেসেজ হ্যান্ডলার (লিঙ্ক চেক ও রিপ্লাই পাঠানো)
@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def link_handler(message: types.Message):
    url = message.text.strip()
    extracted_id, new_link = extract_id_and_generate_link(url)

    if extracted_id:
        buttons = create_inline_buttons(new_link)
        await message.reply(f"✅ **Here's your link:**\n🔗 {new_link}", reply_markup=buttons, parse_mode="Markdown")
    else:
        await message.reply("❌ No valid 'tera' link found!")

# ইনলাইন বোতামের কলব্যাক হ্যান্ডলার
@dp.callback_query_handler(lambda c: c.data.startswith("regenerate") or c.data == "delete")
async def callback_handler(call: types.CallbackQuery):
    if call.data == "delete":
        await call.message.delete()
    elif call.data.startswith("regenerate"):
        old_id = call.data.split(":")[1]
        new_id = old_id[1:]  # প্রথম ক্যারেক্টার বাদ দিয়ে নতুন ID তৈরি
        new_link = f"https://mdiskplay.com/terabox/{new_id}"
        buttons = create_inline_buttons(new_link)

        await call.message.edit_text(f"♻️ **Regenerated Link:**\n🔗 {new_link}", reply_markup=buttons, parse_mode="Markdown")

# বট চালানো
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
