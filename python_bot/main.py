import asyncio
import logging

import os
import re
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from database import TaskDB


logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# TODO: init DB 
db = TaskDB()

@dp.message(Command("start"))
async def start_command_handler(message: Message):
    await message.answer(
        "🤖 Smart Task Bot\n\n"
        "/add \"Купить молоко | 3 | 2026-01-10\" — добавить задачу\n"
        "/list — список задач"
    )

@dp.message(Command("add"))
async def add_task_handler(message: Message):
    if message.text is None:
        await message.answer("Пожалуйста, отправьте текстовое сообщение")
        return
    
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя")
        return
    
    try:
        match = re.match(r'^(.*?)\s*\|\s*(\d+)\s*\|\s*(.+)$', message.text.split(maxsplit=1)[1])
        if not match:
            await message.answer("Формат: /add \"Текст | приоритет(1-5) | YYYY-MM-DD\"")
            return
    
        text, priority, deadline = match.groups()
        priority = int(priority)

        if not 1 <= priority <= 5:
            await message.answer("Приоритет 1-5!")
            return
        
        task_id = await db.add_task(
            message.from_user.id, text.strip(), priority, deadline.strip()
        )

        await message.answer(f"✅ Задача #{task_id} добавлена!\n{text}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("list"))
async def list_task_handler(message: Message):
    # show user's list of tasks
    pass


async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())