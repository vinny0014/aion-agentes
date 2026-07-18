"""Routers CRUD — Usuários, Agentes, Conteúdo e Tarefas."""
from fastapi import APIRouter, Depends, HTTPException, status

from ..core import database as db
from ..core.security import get_current_user, require_admin
from ..schemas import (
    AgentIn, AgentUpdate, ContentIn, ContentUpdate,
    TaskIn, TaskUpdate, UserOut, UserUpdate,
)


def _update(table: str, item_id: int, data: dict, touch: bool = False) -> None:
    fields = {k: v for k, v in data.items() if v is not None}
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nada para atualizar")
    sets = ", ".join(f"{k} = ?" for k in fields)
    if touch:
        sets += ", updated_at = datetime('now')"
    db.execute(f"UPDATE {table} SET {sets} WHERE id = ?", (*fields.values(), item_id))


def _get_or_404(table: str, item_id: int, label: str) -> dict:
    row = db.query_one(f"SELECT * FROM {table} WHERE id = ?", (item_id,))
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{label} não encontrado(a)")
    return row


# ====================== USUÁRIOS (admin) ======================
users_router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(require_admin)])


@users_router.get("", response_model=list[UserOut])
def list_users():
    return db.query("SELECT id, email, name, role, is_active, created_at FROM users ORDER BY id")


@users_router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    row = _get_or_404("users", user_id, "Usuário")
    row.pop("password_hash", None)
    return row


@users_router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate):
    _get_or_404("users", user_id, "Usuário")
    _update("users", user_id, data.model_dump())
    return get_user(user_id)


@users_router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não é possível excluir a própria conta")
    _get_or_404("users", user_id, "Usuário")
    db.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ====================== AGENTES ======================
agents_router = APIRouter(prefix="/api/agents", tags=["agents"])


@agents_router.get("")
def list_agents(user: dict = Depends(get_current_user)):
    return db.query("SELECT * FROM agents ORDER BY id")


@agents_router.post("", status_code=201, dependencies=[Depends(require_admin)])
def create_agent(data: AgentIn):
    if db.query_one("SELECT id FROM agents WHERE slug = ?", (data.slug,)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug já existe")
    aid = db.execute(
        "INSERT INTO agents (slug, name, role, description, status, config_json) VALUES (?,?,?,?,?,?)",
        (data.slug, data.name, data.role, data.description, data.status, data.config_json),
    )
    return _get_or_404("agents", aid, "Agente")


@agents_router.get("/{agent_id}")
def get_agent(agent_id: int, user: dict = Depends(get_current_user)):
    return _get_or_404("agents", agent_id, "Agente")


@agents_router.patch("/{agent_id}", dependencies=[Depends(require_admin)])
def update_agent(agent_id: int, data: AgentUpdate):
    _get_or_404("agents", agent_id, "Agente")
    _update("agents", agent_id, data.model_dump())
    return _get_or_404("agents", agent_id, "Agente")


@agents_router.delete("/{agent_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_agent(agent_id: int):
    _get_or_404("agents", agent_id, "Agente")
    db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))


# ====================== CONTEÚDO ======================
content_router = APIRouter(prefix="/api/contents", tags=["contents"])


@content_router.get("")
def list_contents(status_f: str | None = None, user: dict = Depends(get_current_user)):
    if status_f:
        return db.query("SELECT * FROM contents WHERE status = ? ORDER BY id DESC", (status_f,))
    return db.query("SELECT * FROM contents ORDER BY id DESC")


@content_router.post("", status_code=201)
def create_content(data: ContentIn, user: dict = Depends(get_current_user)):
    if db.query_one("SELECT id FROM contents WHERE slug = ?", (data.slug,)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug já existe")
    pub = "datetime('now')" if data.status == "published" else "NULL"
    img, alt = data.image_url, data.image_alt
    if not img:  # regra absoluta: nenhum artigo sem imagem
        from ..agents.imagegen import editorial_data_uri
        img = editorial_data_uri(data.title, data.category or "news")
        alt = alt or f"AION editorial artwork: {data.title[:90]}"
    cid = db.execute(
        f"""INSERT INTO contents (title, slug, body, excerpt, status, author_id, agent_id,
            seo_title, seo_description, category, tags, author, image_url, image_alt,
            image_credit, image_width, image_height, featured, pinned, breaking_flag,
            editors_pick, scheduled_at, source_url, published_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'1200','630',?,?,?,?,?,?,{pub})""",
        (data.title, data.slug, data.body, data.excerpt, data.status,
         user["id"], data.agent_id, data.seo_title or data.title,
         data.seo_description or data.excerpt, data.category.strip().lower(),
         ",".join(t.strip().lower() for t in data.tags.split(",") if t.strip()),
         data.author or "AION Editorial", img, alt or f"Image: {data.title[:90]}",
         "AION editorial artwork" if not data.image_url else "",
         data.featured, data.pinned, data.breaking_flag, data.editors_pick,
         data.scheduled_at, data.source_url),
    )
    return _get_or_404("contents", cid, "Article")


@content_router.get("/{content_id}")
def get_content(content_id: int, user: dict = Depends(get_current_user)):
    return _get_or_404("contents", content_id, "Article")


@content_router.patch("/{content_id}")
def update_content(content_id: int, data: ContentUpdate, user: dict = Depends(get_current_user)):
    row = _get_or_404("contents", content_id, "Article")
    _update("contents", content_id, data.model_dump(), touch=True)
    if data.featured or data.breaking_flag:  # imagem do hero recalculada ao destacar
        from ..agents.team import compute_hero_image
        compute_hero_image(content_id)
    if data.status == "published" and row["status"] != "published":
        db.execute("UPDATE contents SET published_at = datetime('now') WHERE id = ?", (content_id,))
    return _get_or_404("contents", content_id, "Article")


@content_router.delete("/{content_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_content(content_id: int):
    _get_or_404("contents", content_id, "Article")
    db.execute("DELETE FROM contents WHERE id = ?", (content_id,))


# ====================== TAREFAS ======================
tasks_router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@tasks_router.get("")
def list_tasks(user: dict = Depends(get_current_user)):
    return db.query("SELECT * FROM tasks ORDER BY priority ASC, id DESC")


@tasks_router.post("", status_code=201)
def create_task(data: TaskIn, user: dict = Depends(get_current_user)):
    tid = db.execute(
        """INSERT INTO tasks (title, description, status, priority, agent_id, assignee_id, due_at)
           VALUES (?,?,?,?,?,?,?)""",
        (data.title, data.description, data.status, data.priority,
         data.agent_id, data.assignee_id, data.due_at),
    )
    return _get_or_404("tasks", tid, "Tarefa")


@tasks_router.get("/{task_id}")
def get_task(task_id: int, user: dict = Depends(get_current_user)):
    return _get_or_404("tasks", task_id, "Tarefa")


@tasks_router.patch("/{task_id}")
def update_task(task_id: int, data: TaskUpdate, user: dict = Depends(get_current_user)):
    _get_or_404("tasks", task_id, "Tarefa")
    _update("tasks", task_id, data.model_dump(), touch=True)
    return _get_or_404("tasks", task_id, "Tarefa")


@tasks_router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, user: dict = Depends(get_current_user)):
    _get_or_404("tasks", task_id, "Tarefa")
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
