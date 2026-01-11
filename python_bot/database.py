import aiosqlite
import datetime


class TaskDB:
    def __init__(self, db_path : str = "tasks.db"):
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
            row = await cursor.fetchone()
            return int(row[0]) if row is not None else 0
            # Check if 0 -> fail to add
    
    async def get_user_tasks(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, text, priority, deadline, status, created_at
                FROM tasks
                WHERE user_id = ?
                ORDER BY status ASC, priority DESC, deadline ASC
                """,
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_task_status(self, task_id: int, user_id: int, status: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE tasks
                SET status = ?
                WHERE id = ? AND user_id = ?
                """,
                (status, task_id, user_id)
            )
            await db.commit()

            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT status FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id)
            )
            row = await cursor.fetchone()
            return row is not None and row["status"] == status
