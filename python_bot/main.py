import asyncio
import logging

import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message


logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# TODO: init DB 

@dp.message(Command("start"))
async def start_command_handler(message: Message):
    await message.answer(
        "🤖 Smart Task Bot\n\n"
        "/add \"Купить молоко | 3 | 2026-01-10\" — добавить задачу\n"
        "/list — список задач"
    )

@dp.message(Command("add"))
async def add_task_handler(message: Message):
    # TODO: Check if usage is valid and add task to tasklist
    try:
        print()
    except:
        print()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())