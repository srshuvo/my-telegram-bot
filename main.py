import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, CallbackQuery

TOKEN = "YOUR_BOT_TOKEN_HERE"  # 🔴 এখানে আপনার বটের টোকেন ব্যবহার করুন

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


def extract_id_from_url(url):
    """ 🔍 লিংকে 'tera' থাকলে, ID বের করবে """
    if "tera" in url:
        match = re.search(r"/s/([a-zA-Z0-9]+)", url)
        return match.group(1) if match else None
    return None


def modify_id(original_id):
    """ 🔄 Regenerate: ID-এর প্রথম ১টি অক্ষর বাদ দিয়ে নতুন আইডি তৈরি করবে """
    return original_id[1:] if original_id and len(original_id) > 1 else None


async def send_modified_link(message: Message, file_id):
    """ ✅ নতুন লিংক তৈরি করে ইনলাইন বোতাম সহ পাঠাবে """
    new_url = f"https://mdiskplay.com/terabox/{file_id}"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🎬 Watch Video", url=new_url)
    keyboard.button(text="🔗 Share", switch_inline_query=new_url)
    keyboard.button(text="🔄 Regenerate", callback_data=f"regenerate_{file_id}")
    keyboard.button(text="🗑️ Delete", callback_data="delete_message")
    keyboard.adjust(1)

    await message.reply("✅ আপনার লিংক প্রস্তুত!", reply_markup=keyboard.as_markup())


@dp.message(F.text)
async def modify_link(message: Message):
    """ ✅ ইউজারের পাঠানো লিংক থেকে ID বের করে নতুন লিংক তৈরি করবে """
    text = message.text
    if not text:
        return

    urls = text.split()
    for url in urls:
        file_id = extract_id_from_url(url)
        if file_id:
            await send_modified_link(message, file_id)
            return

    await message.reply("⚠️ কোনো বৈধ লিংক পাওয়া যায়নি!")


@dp.callback_query(F.data.startswith("regenerate_"))
async def regenerate_link(callback: CallbackQuery):
    """ 🔄 Regenerate বাটন: নতুন আইডি তৈরি করবে """
    old_id = callback.data.split("_")[1]
    new_id = modify_id(old_id)

    if not new_id:
        await callback.answer("⚠️ Regenerate সম্ভব না!", show_alert=True)
        return

    await callback.message.delete()
    await send_modified_link(callback.message, new_id)
    await callback.answer("✅ লিংক নতুনভাবে পরিবর্তন করা হয়েছে!")


@dp.callback_query(F.data == "delete_message")
async def delete_message(callback: CallbackQuery):
    """ 🗑️ Delete বোতাম ক্লিক করলে মেসেজ ডিলিট করবে """
    await callback.message.delete()
    await callback.answer("✅ মেসেজ মুছে ফেলা হয়েছে!", show_alert=True)


async def main():
    """ 🚀 বট চালানোর ফাংশন """
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
