from database import get_conn, now, row_to_dict

class TaskManager:
    def create_task(self, title: str, description: str):
        ts = now()
        with get_conn() as conn:
            cur = conn.execute(
                'INSERT INTO tasks(title, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                (title, description, 'created', ts, ts)
            )
            task_id = cur.lastrowid
        return self.get_task(task_id)

    def get_task(self, task_id: int):
        with get_conn() as conn:
            return row_to_dict(conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone())

    def list_tasks(self):
        with get_conn() as conn:
            return [row_to_dict(r) for r in conn.execute('SELECT * FROM tasks ORDER BY id DESC')]

    def update_task(self, task_id: int, **fields):
        fields['updated_at'] = now()
        keys = ', '.join([f'{k}=?' for k in fields.keys()])
        values = list(fields.values()) + [task_id]
        with get_conn() as conn:
            conn.execute(f'UPDATE tasks SET {keys} WHERE id=?', values)
        return self.get_task(task_id)

    def add_step(self, task_id: int, order: int, title: str, status: str, details: str):
        with get_conn() as conn:
            conn.execute(
                'INSERT INTO task_steps(task_id, step_order, title, status, details, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (task_id, order, title, status, details, now())
            )

    def list_steps(self, task_id: int):
        with get_conn() as conn:
            return [row_to_dict(r) for r in conn.execute('SELECT * FROM task_steps WHERE task_id=? ORDER BY step_order ASC, id ASC', (task_id,))]

    def save_report(self, task_id: int, report: str):
        with get_conn() as conn:
            conn.execute('INSERT INTO task_reports(task_id, report, created_at) VALUES (?, ?, ?)', (task_id, report, now()))

    def get_report(self, task_id: int):
        with get_conn() as conn:
            row = conn.execute('SELECT * FROM task_reports WHERE task_id=? ORDER BY id DESC LIMIT 1', (task_id,)).fetchone()
            return row_to_dict(row)

    def log(self, task_id, level: str, message: str):
        with get_conn() as conn:
            conn.execute('INSERT INTO task_logs(task_id, level, message, created_at) VALUES (?, ?, ?, ?)', (task_id, level, message, now()))

    def list_logs(self):
        with get_conn() as conn:
            return [row_to_dict(r) for r in conn.execute('SELECT * FROM task_logs ORDER BY id DESC LIMIT 200')]
