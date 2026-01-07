import aiosqlite
import asyncio
import datetime
from typing import List, Dict, Any


class TaskDB:
    def __init__(self, db_path : str = "tasts.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    text TEXT,
                    priority INTEGER,
                    deadline TEXT,
                    status TEXT DEFAULT 'todo',
                    created_at TEXT
                )
            """)
            await db.commit()
    
    async def add_task(self, user_id: int, text: str, priority: int, deadline: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            
            await db.execute(
                "INSERT INTO tasks (user_id, text, priority, deadline, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, text, priority, deadline, datetime.datetime.now().isoformat())
            )
            await db.commit()
            cursor = await db.execute("SELECT last_insert_rowid()")
            return cursor.lastrowid or 0
            # Check if 0 -> fail to add
    
    async def get_user_tasks(self, user_id: int):
        pass
        #return list of user[user_id] tasks
