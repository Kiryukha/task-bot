import asyncio
import logging

import os
import re
from dotenv import load_dotenv

import datetime as dt

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

user_settings: dict[int, dict[str, bool]] = {}

def should_show_done(user_id: int) -> bool:
    return user_settings.get(user_id, {}).get("show_done", True)


@dp.message(Command("start"))
async def start_command_handler(message: Message):
    await message.answer(
        "🤖 Smart Task Bot\n\n"
        "/add Купить молоко | 3 | 2026-01-10 — добавить задачу\n"
        "/list — список задач\n"
        "/done <id> — отметить задачу как выполненную\n"
        "/delete <id> — удалить задачу\n"
        "/hide_done — скрыть выполненные в /list\n"
        "/show_done — показывать выполненные в /list"
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

        try:
            dt.date.fromisoformat(deadline.strip())
        except ValueError:
            await message.answer("Дата должна быть в формате YYYY-MM-DD, пример: 2026-01-10")
            return

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

    active = [t for t in tasks if t["status"] != "done"]
    done = [t for t in tasks if t["status"] == "done"]

    lines: list[str] = []

    if active:
        lines.append("⏳ Активные задачи:\n")
        for t in active:
            lines.append(
                f"#{t['id']} | {t['text']} "
                f"(приоритет {t['priority']}) | дедлайн {t['deadline']}"
            )
        lines.append("")

    show_done = should_show_done(message.from_user.id)

    if done and show_done:
        lines.append("✅ Выполненные задачи:\n")
        for t in done:
            lines.append(
                f"#{t['id']} | {t['text']} "
                f"(приоритет {t['priority']}) | дедлайн {t['deadline']}"
            )
    
    if not active and done and not show_done:
        lines = ["🎉 Все задачи выполнены"]

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


@dp.message(Command("hide_done"))
async def hide_done_handler(message: Message):
    if message.from_user is None:
        return
    uid = message.from_user.id
    user_settings.setdefault(uid, {})["show_done"] = False
    await message.answer("✅ Выполненные задачи теперь скрыты в /list")

@dp.message(Command("show_done"))
async def show_done_handler(message: Message):
    if message.from_user is None:
        return
    uid = message.from_user.id
    user_settings.setdefault(uid, {})["show_done"] = True
    await message.answer("✅ Выполненные задачи теперь показываются в /list")


@dp.message(Command("delete"))
async def delete_task_handler(message: Message):
    if message.text is None or message.from_user is None:
        await message.answer("Неверный формат команды")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /delete <id задачи>")
        return

    try:
        task_id = int(parts[1])
    except ValueError:
        await message.answer("id задачи должен быть числом. Пример: /delete 3")
        return

    deleted = await db.delete_task(task_id, message.from_user.id)
    if deleted:
        await message.answer(f"🗑 Задача #{task_id} удалена")
    else:
        await message.answer("Задача не найдена")


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "Команды:\n"
        "/add ... — добавить задачу\n"
        "/list — показать задачи\n"
        "/done <id> — выполнить\n"
        "/delete <id> — удалить\n"
        "/hide_done /show_done — скрыть/показать выполненные\n"
    )


async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())