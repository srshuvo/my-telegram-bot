import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import re
import os

TOKEN = "YOUR_BOT_TOKEN"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://your-render-app.onrender.com{WEBHOOK_PATH}"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    if message.text:
        match = re.search(r"tera(?:box)?[^"]*?([a-zA-Z0-9]+)", message.text)
        if match:
            file_id = match.group(1)
            new_link = f"https://mdiskplay.com/terabox/{file_id}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎬 Watch Video", url=new_link)],
                [InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"regen_{file_id}")],
                [InlineKeyboardButton(text="❌ Delete", callback_data="delete")]
            ])
            await message.answer(f"Here is your link: {new_link}", reply_markup=keyboard)

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    if callback.data.startswith("regen_"):
        file_id = callback.data.split("_")[1][1:]
        new_link = f"https://mdiskplay.com/terabox/{file_id}"
        await callback.message.edit_text(f"Regenerated link: {new_link}", reply_markup=callback.message.reply_markup)
    elif callback.data == "delete":
        await callback.message.delete()
    await callback.answer()

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("Webhook set successfully!")

async def on_shutdown():
    await bot.delete_webhook()
    logging.info("Webhook deleted successfully!")

app = web.Application()
app.on_startup.append(lambda _: on_startup())
app.on_shutdown.append(lambda _: on_shutdown())

SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
