import os
import re
import asyncio
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from flask import Flask

# ✅ Environment variables লোড করা
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ Bot & Dispatcher সেটআপ (aiogram v3.7+ অনুযায়ী)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# ✅ Flask Web Server তৈরি
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ✅ শুধুমাত্র 'tera' থাকা লিংক পরিবর্তন করবে
def extract_ids_and_generate_links(text):
    matches = re.findall(r"https?://\S+", text)  # সমস্ত লিংক বের করা
    unique_links = {link for link in matches if "tera" in link}  # শুধু 'tera' থাকা লিংক নেবে
    link_map = {link: f"https://mdiskplay.com/terabox/{link.split('/')[-1]}" for link in unique_links}  # নতুন লিংক তৈরি
    return link_map

# ✅ ইনলাইন বোতাম তৈরি ফাংশন
def create_inline_buttons(link_map):
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎬 Watch Video {i+1}", url=new_link)] +
        [InlineKeyboardButton(text="🔗 Share", switch_inline_query=new_link)] +
        [InlineKeyboardButton(text="🗑️ Delete", callback_data=f"delete:{new_link.split('/')[-1]}")] +
        [InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"regenerate:{new_link.split('/')[-1]}")]
        for i, (old_link, new_link) in enumerate(link_map.items())
    ])
    return buttons

# ✅ Start command
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Welcome! Send me a 'tera' link or a media with a 'tera' link, and I'll generate a new link for you.")

# ✅ মেসেজ হ্যান্ডলার (টেক্সট বা মিডিয়া ক্যাপশন চেক)
@dp.message()
async def link_handler(message: types.Message):
    text = message.text if message.text else message.caption  # টেক্সট বা ক্যাপশন চেক
    if not text:
        return  # যদি টেক্সট বা ক্যাপশন না থাকে, কিছু করবে না

    link_map = extract_ids_and_generate_links(text)

    if link_map:
        buttons = create_inline_buttons(link_map)
        modified_links = "\n".join([f"🔗 {new_link}" for new_link in link_map.values()])
        await message.answer(f"✅ **Modified Links:**\n{modified_links}", reply_markup=buttons)
    else:
        await message.answer("❌ No valid 'tera' link found!")

# ✅ ইনলাইন বোতামের কলব্যাক হ্যান্ডলার
@dp.callback_query()
async def callback_handler(call: CallbackQuery):
    if call.data.startswith("delete"):
        await call.message.delete()
    elif call.data.startswith("regenerate"):
        old_id = call.data.split(":")[1]
        new_id = old_id[1:]  # প্রথম ক্যারেক্টার বাদ দিয়ে নতুন ID তৈরি
        new_link = f"https://mdiskplay.com/terabox/{new_id}"
        buttons = create_inline_buttons({new_id: new_link})

        await call.message.edit_text(f"♻️ **Regenerated Link:**\n🔗 {new_link}", reply_markup=buttons)

# ✅ মেইন ফাংশন (aiogram v3 অনুযায়ী async loop সেটআপ)
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Flask Server চালু করা
    asyncio.run(main())  # Telegram Bot চালু করা
