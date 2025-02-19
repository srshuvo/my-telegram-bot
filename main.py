import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web
import logging

# Environment variables
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# Create bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Link and ID extraction function
def extract_id(url):
    match = re.search(r"tera(\d+)", url)
    if match:
        return match.group(1)
    return None

# Regenerate function
def regenerate_id(old_id):
    return old_id[1:]

# Command to start the bot
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Send a link containing 'tera' to get started!")

# Function to handle incoming links
@dp.message_handler(lambda message: 'tera' in message.text)
async def handle_tera_link(message: types.Message):
    extracted_id = extract_id(message.text)
    if extracted_id:
        new_link = f"https://mdiskplay.com/terabox/{extracted_id}"
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text="🎬 Watch Video", url=new_link),
            InlineKeyboardButton(text="🔗 Share", switch_inline_query="Share"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data="delete"),
            InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"regenerate:{extracted_id}")
        )
        await message.answer("🎬 Watch Video → " + new_link, reply_markup=keyboard)

# Handle callback for regeneration
@dp.callback_query_handler(lambda c: c.data.startswith('regenerate:'))
async def regenerate_link(callback_query: types.CallbackQuery):
    old_id = callback_query.data.split(":")[1]
    new_id = regenerate_id(old_id)
    new_link = f"https://mdiskplay.com/terabox/{new_id}"
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🎬 Watch Video", url=new_link),
        InlineKeyboardButton(text="🔗 Share", switch_inline_query="Share"),
        InlineKeyboardButton(text="🗑️ Delete", callback_data="delete"),
        InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"regenerate:{new_id}")
    )
    await bot.edit_message_text(
        f"🎬 Watch Video → {new_link}",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )

# -------------- Main ফাংশন: ওয়েব সার্ভার ও বটের পোলিং শুরু করা --------------
async def main():
    # Start the webserver in a separate task
    asyncio.create_task(start_webserver())
    logger.info("✅ Bot is starting polling...")
    # Start bot polling
    await dp.start_polling()

if __name__ == "__main__":
    # Run everything inside asyncio loop
    asyncio.run(main())
