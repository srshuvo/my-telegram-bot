from contextlib import asynccontextmanager
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn

# ✅ Environment variables লোড করা
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Webhook URL

# ✅ Bot & Dispatcher সেটআপ (aiogram v3)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))
dp = Dispatcher()

# ✅ Lifespan Event Handler (নতুন Startup System)
@asynccontextmanager
async def lifespan(app: FastAPI):
    if WEBHOOK_URL:  # Ensure WEBHOOK_URL is not None
        try:
            await bot.set_webhook(WEBHOOK_URL)
            print(f"✅ Webhook set to: {WEBHOOK_URL}")
        except Exception as e:
            print(f"❌ Failed to set webhook: {e}")
    else:
        print("⚠️ WEBHOOK_URL is not set! Bot will not receive updates.")

    yield  # FastAPI চালানোর জন্য প্রয়োজনীয় অংশ

# ✅ FastAPI server setup
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def home():
    return {"message": "Bot is running on Webhook!"}

# ✅ FastAPI রাউটার থেকে Webhook কল হবে
@app.post(f"/{BOT_TOKEN}")
async def webhook(request: Request):
    json_str = await request.json()
    update = types.Update(**json_str)
    await dp.process_update(update)
    return {"status": "ok"}

# ✅ Render এর পোর্ট নিয়ন্ত্রণ
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render থেকে দেওয়া পোর্ট ব্যবহার
    uvicorn.run(app, host="0.0.0.0", port=port)  # Webhook সার্ভার চালানো
