import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Environment variables লোড করা
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Bot & Dispatcher সেটআপ (aiogram v3.7+ অনুযায়ী)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

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
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Watch Video", url=link)],
        [InlineKeyboardButton(text="🔗 Share", switch_inline_query=link)],
        [InlineKeyboardButton(text="🗑️ Delete", callback_data="delete"),
         InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"regenerate:{link.split('/')[-1]}")]
    ])
    return buttons

# Start command
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Welcome! Send me a link containing 'tera' and I'll generate a new link for you.")

# মেসেজ হ্যান্ডলার (লিঙ্ক চেক ও রিপ্লাই পাঠানো)
@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    extracted_id, new_link = extract_id_and_generate_link(url)

    if extracted_id:
        buttons = create_inline_buttons(new_link)
        await message.answer(f"✅ **Here's your link:**\n🔗 {new_link}", reply_markup=buttons)
    else:
        await message.answer("❌ No valid 'tera' link found!")

# ইনলাইন বোতামের কলব্যাক হ্যান্ডলার
@dp.callback_query()
async def callback_handler(call: CallbackQuery):
    if call.data == "delete":
        await call.message.delete()
    elif call.data.startswith("regenerate"):
        old_id = call.data.split(":")[1]
        new_id = old_id[1:]  # প্রথম ক্যারেক্টার বাদ দিয়ে নতুন ID তৈরি
        new_link = f"https://mdiskplay.com/terabox/{new_id}"
        buttons = create_inline_buttons(new_link)

        await call.message.edit_text(f"♻️ **Regenerated Link:**\n🔗 {new_link}", reply_markup=buttons)

# মেইন ফাংশন (aiogram v3 অনুযায়ী async loop সেটআপ)
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
