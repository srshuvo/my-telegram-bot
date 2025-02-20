import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import re
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Helper function to extract ID from Terabox link
def extract_id(link):
    match = re.search(r"terabox.com/s/([a-zA-Z0-9_]+)", link)  # _ added to regex
    if match:
        return match.group(1)
    return None

# Handler for /start command
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Welcome! Send a Terabox link to extract ID and generate a new link.")

# Handler for text messages with Terabox link
@dp.message_handler(regexp=r"https://www\.terabox\.com/s/[a-zA-Z0-9_]+")  # _ added to regex
async def handle_terabox_link(message: types.Message):
    link = message.text
    extracted_id = extract_id(link)
    if extracted_id:
        new_link = f"https://mdiskplay.com/terabox/{extracted_id}"
        
        # Sending message with inline buttons
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("▶️ Watch Video", url=new_link),
            types.InlineKeyboardButton("🔗 Share", url=new_link),
            types.InlineKeyboardButton("♻️ Regenerate", callback_data=f"regenerate_{extracted_id}"),
            types.InlineKeyboardButton("❌ Delete", callback_data="delete")
        )
        await message.reply(f"✅ New link generated:\n🔗 {new_link}", reply_markup=markup)
    else:
        await message.reply("❌ Invalid Terabox link. Please try again.")

# Handler for inline button actions
@dp.callback_query_handler(lambda c: c.data.startswith("regenerate_"))
async def regenerate_id(callback_query: types.CallbackQuery):
    old_id = callback_query.data.split("_")[1]
    new_id = old_id[1:]  # Removing the first character to regenerate
    new_link = f"https://mdiskplay.com/terabox/{new_id}"

    # Update message with new link
    await bot.edit_message_text(
        f"✅ New link generated:\n🔗 {new_link}",
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("▶️ Watch Video", url=new_link),
            types.InlineKeyboardButton("🔗 Share", url=new_link),
            types.InlineKeyboardButton("♻️ Regenerate", callback_data=f"regenerate_{new_id}"),
            types.InlineKeyboardButton("❌ Delete", callback_data="delete")
        )
    )

# Handler for delete action
@dp.callback_query_handler(lambda c: c.data == "delete")
async def delete_message(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
