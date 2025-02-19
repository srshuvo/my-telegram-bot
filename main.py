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

# ✅ শুধু 'tera' লেখা থাকা লিংক ফিল্টার করে ID বের করবে এবং নতুন লিংক তৈরি করবে
def extract_ids_and_generate_links(text):
    matches = re.findall(r"https?://\S*/(\S*tera\S*)", text)  # শুধু 'tera' থাকা লিংক নেবে
    unique_links = set(matches)  # ইউনিক আইডি বের করা
    link_map = {id_: f"https://mdiskplay.com/terabox/{id_}" for id_ in unique_links}  # নতুন লিংক তৈরি
    return link_map

# ✅ ইনলাইন বোতাম তৈরি ফাংশন
def create_inline_buttons(link_map):
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🎬 Watch Video {i+1}", url=new_link),
            InlineKeyboardButton(text="🔗 Share", switch_inline_query=new_link),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"delete:{new_link}"),
            InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"regenerate:{new_link}")
        ]
        for i, (old_id, new_link) in enumerate(link_map.items())
    ])
    return buttons

# ✅ Start command
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Welcome! Send me a link or a media with a link, and I'll generate a new link for you.")

# ✅ লিংক চেকার (টেক্সট বা মিডিয়া ক্যাপশন চেক)
@dp.message()
async def link_handler(message: types.Message):
    text = message.text if message.text else message.caption  # টেক্সট বা ক্যাপশন চেক
    if not text:
        return  # লিংক না থাকলে কিছু করবে না

    link_map = extract_ids_and_generate_links(text)  # লিংক বের করে নতুন লিংক তৈরি করা

    if link_map:
        buttons = create_inline_buttons(link_map)
        modified_links = "\n".join([f"🔗 {new_link}" for new_link in link_map.values()])
        await message.answer(f"✅ **Modified Links:**\n{modified_links}", reply_markup=buttons)
    else:
        await message.answer("❌ No valid 'tera' link found!")

# ✅ ইনলাইন বোতামের কলব্যাক হ্যান্ডলার (Regenerate ঠিক করা হয়েছে)
@dp.callback_query()
async def callback_handler(call: CallbackQuery):
    if call.data.startswith("delete"):
        await call.message.delete()

    elif call.data.startswith("regenerate"):
        old_link = call.data.split(":")[1]  # পুরাতন লিংক
        old_id = old_link.split("/")[-1]  # পুরাতন ID

        # যদি ID এক অক্ষরের হয়, তাহলে পরিবর্তন না করে আগেরটাই থাকবে
        if len(old_id) > 1:
            new_id = old_id[1:]  # প্রথম ক্যারেক্টার বাদ দিয়ে নতুন ID তৈরি
        else:
            new_id = old_id  # ID ছোট হলে পরিবর্তন হবে না

        new_link = f"https://mdiskplay.com/terabox/{new_id}"  # নতুন লিংক
        
        # আগের মেসেজ থেকে সমস্ত লিংক বের করা
        original_text = call.message.text
        existing_links = re.findall(r"https://mdiskplay.com/terabox/\S+", original_text)

        # পুরাতন লিংক আপডেট করে নতুন লিংক বসানো
        updated_links = [new_link if link == old_link else link for link in existing_links]
        updated_text = "✅ **Modified Links:**\n" + "\n".join([f"🔗 {link}" for link in updated_links])

        # নতুন বোতাম সেটআপ
        new_link_map = {link: link for link in updated_links}
        buttons = create_inline_buttons(new_link_map)

        await call.message.edit_text(updated_text, reply_markup=buttons)

# ✅ মেইন ফাংশন (aiogram v3 অনুযায়ী async loop সেটআপ)
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    import uvicorn
from fastapi import FastAPI

# ✅ FastAPI server setup (Webhook না থাকলেও HTTP সার্ভার চালাবে, Render-এর পোর্ট সমস্যা সমাধান করবে)
app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Bot is running!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render-এর জন্য পোর্ট সেট করুন
    asyncio.create_task(main())  # Bot চালানো
    uvicorn.run(app, host="0.0.0.0", port=port)  # HTTP সার্ভার চালানো
