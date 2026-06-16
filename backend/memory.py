from database import get_conn, now, row_to_dict

class MemoryStore:
    def save(self, task_id: int, key: str, value: str):
        with get_conn() as conn:
            conn.execute(
                'INSERT INTO task_memory(task_id, memory_key, memory_value, created_at) VALUES (?, ?, ?, ?)',
                (task_id, key, value, now())
            )

    def list_all(self):
        with get_conn() as conn:
            return [row_to_dict(r) for r in conn.execute('SELECT * FROM task_memory ORDER BY id DESC LIMIT 200')]
