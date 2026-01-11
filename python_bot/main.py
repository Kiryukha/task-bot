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

db = TaskDB()

@dp.message(Command("start"))
async def start_command_handler(message: Message):
    await message.answer(
        "🤖 Smart Task Bot\n\n"
        "/add Купить молоко | 3 | 2026-01-10 — добавить задачу\n"
        "/list — список задач"
        "/done 1 - отметить задачу как выполненную"
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
            await message.answer("Формат: /add Текст | приоритет(1-5) | YYYY-MM-DD")
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
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя")
        return

    tasks = await db.get_user_tasks(message.from_user.id)
    if not tasks:
        await message.answer("📝 У тебя пока нет задач")
        return

    lines = ["📋 Твои задачи:\n"]
    for task in tasks:
        status_icon = "✅" if task["status"] == "done" else "⏳"
        lines.append(
            f"{status_icon} #{task['id']} | {task['text']} "
            f"(приоритет {task['priority']}) | дедлайн {task['deadline']}"
        )

    await message.answer("\n".join(lines))


@dp.message(Command("done"))
async def done_task_handler(message: Message):
    if message.text is None or message.from_user is None:
        await message.answer("Неверный формат команды")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /done <id задачи>")
        return

    try:
        task_id = int(parts[1])
    except ValueError:
        await message.answer("id задачи должен быть числом. Пример: /done 3")
        return

    updated = await db.update_task_status(task_id, message.from_user.id, "done")
    if not updated:
        await message.answer("Задача не найдена или уже обновлена")
    else:
        await message.answer(f"✅ Задача #{task_id} помечена как выполненная")


@dp.message(Command("debug_tasks"))
async def debug_tasks_handler(message: Message):
    if message.text is None or message.from_user is None:
        await message.answer("Неверный формат команды")
        return
     
    tasks = await db.get_user_tasks(message.from_user.id)
    if not tasks:
        await message.answer("DEBUG: задач нет")
        return

    lines = ["DEBUG задачи:\n"]
    for t in tasks:
        lines.append(
            f"id={t['id']}, user_id={message.from_user.id}, "
            f"text={t['text']}, status={t['status']}"
        )
    await message.answer("\n".join(lines))


async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())