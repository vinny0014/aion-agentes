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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")
    sets = ", ".join(f"{k} = ?" for k in fields)
    if touch:
        sets += ", updated_at = datetime('now')"
    db.execute(f"UPDATE {table} SET {sets} WHERE id = ?", (*fields.values(), item_id))


def _get_or_404(table: str, item_id: int, label: str) -> dict:
    row = db.query_one(f"SELECT * FROM {table} WHERE id = ?", (item_id,))
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{label} not found")
    return row


# ====================== USUÁRIOS (admin) ======================
users_router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(require_admin)])


@users_router.get("", response_model=list[UserOut])
def list_users():
    return db.query("SELECT id, email, name, role, is_active, created_at FROM users ORDER BY id")


@users_router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    row = _get_or_404("users", user_id, "User")
    row.pop("password_hash", None)
    return row


@users_router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate):
    _get_or_404("users", user_id, "User")
    _update("users", user_id, data.model_dump())
    return get_user(user_id)


@users_router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete your own account")
    _get_or_404("users", user_id, "User")
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
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already exists")
    aid = db.execute(
        "INSERT INTO agents (slug, name, role, description, status, config_json) VALUES (?,?,?,?,?,?)",
        (data.slug, data.name, data.role, data.description, data.status, data.config_json),
    )
    return _get_or_404("agents", aid, "Agent")


@agents_router.get("/{agent_id}")
def get_agent(agent_id: int, user: dict = Depends(get_current_user)):
    return _get_or_404("agents", agent_id, "Agent")


@agents_router.patch("/{agent_id}", dependencies=[Depends(require_admin)])
def update_agent(agent_id: int, data: AgentUpdate):
    _get_or_404("agents", agent_id, "Agent")
    _update("agents", agent_id, data.model_dump())
    return _get_or_404("agents", agent_id, "Agent")


@agents_router.delete("/{agent_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_agent(agent_id: int):
    _get_or_404("agents", agent_id, "Agent")
    db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))


# ====================== CONTEÚDO ======================
content_router = APIRouter(prefix="/api/contents", tags=["contents"])


@content_router.get("")
def list_contents(status_f: str | None = None, user: dict = Depends(get_current_user)):
    if status_f:
        return db.query("SELECT * FROM contents WHERE status = ? ORDER BY id DESC", (status_f,))
    return db.query("SELECT * FROM contents ORDER BY id DESC")


@content_router.post("", status_code=201)
def create_content(data: ContentIn, user: dict = Depends(require_admin)):
    if db.query_one("SELECT id FROM contents WHERE slug = ?", (data.slug,)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already exists")
    pub = "datetime('now')" if data.status == "published" else "NULL"
    img, alt = data.image_url.strip(), data.image_alt.strip()
    image_credit = ""
    if data.status == "published":
        from ..agents.imagegen import publication_image
        prepared = publication_image(img, data.title)
        if not prepared:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "Publication blocked: provide a valid HTTP/HTTPS raster image of at least 600x315",
            )
        img = prepared["image_url"]
        alt = alt or f"Editorial image for {data.title[:90]}"
        image_credit = "Source image processed by AION"
        from ..content_rules import publication_issues
        candidate = data.model_dump()
        candidate["image_url"] = img
        if issues := publication_issues(candidate):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                                f"Publication blocked: {'; '.join(issues)}")
    elif img and not img.startswith(("http://", "https://")):
        img = ""
    cid = db.execute(
        f"""INSERT INTO contents (title, slug, body, excerpt, status, author_id, agent_id,
            seo_title, seo_description, category, tags, author, image_url, image_alt,
            image_credit, image_width, image_height, featured, pinned, breaking_flag,
            editors_pick, scheduled_at, source_url, published_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'1200','630',?,?,?,?,?,?,{pub})""",
        (data.title, data.slug, data.body, data.excerpt, data.status,
         user["id"], data.agent_id, (data.seo_title or data.title)[:60],
         (data.seo_description or data.excerpt)[:160], data.category.strip().lower(),
         ",".join(t.strip().lower() for t in data.tags.split(",") if t.strip()),
         data.author or "AION Editorial", img, alt or f"Image: {data.title[:90]}",
         image_credit,
         data.featured, data.pinned, data.breaking_flag, data.editors_pick,
         data.scheduled_at, data.source_url),
    )
    if data.status == "published":
        db.execute(
            "UPDATE contents SET hero_image_url=image_url, hero_image_alt=image_alt, "
            "hero_image_credit=image_credit, hero_image_width='1200', hero_image_height='630', "
            "hero_image_source='primary' WHERE id=?",
            (cid,),
        )
    return _get_or_404("contents", cid, "Content")


@content_router.get("/{content_id}")
def get_content(content_id: int, user: dict = Depends(get_current_user)):
    return _get_or_404("contents", content_id, "Content")


@content_router.patch("/{content_id}")
def update_content(content_id: int, data: ContentUpdate, user: dict = Depends(require_admin)):
    row = _get_or_404("contents", content_id, "Content")
    changes = data.model_dump()
    target_status = data.status or row["status"]
    if target_status == "published":
        from ..agents.imagegen import publication_image
        candidate = data.image_url if data.image_url is not None else row["image_url"]
        title = data.title or row["title"]
        prepared = publication_image(candidate or "", title)
        if not prepared:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "Publication blocked: provide a valid HTTP/HTTPS raster image of at least 600x315",
            )
        changes["image_url"] = prepared["image_url"]
        changes["image_alt"] = data.image_alt or row["image_alt"] or f"Editorial image for {title[:90]}"
        from ..content_rules import publication_issues
        candidate_row = {**row, **{key: value for key, value in changes.items() if value is not None}}
        if issues := publication_issues(candidate_row):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                                f"Publication blocked: {'; '.join(issues)}")
    elif data.image_url is not None and not data.image_url.startswith(("http://", "https://")):
        changes["image_url"] = ""
    _update("contents", content_id, changes, touch=True)
    if target_status == "published":
        db.execute(
            "UPDATE contents SET image_width='1200', image_height='630', "
            "hero_image_url=image_url, hero_image_alt=image_alt, hero_image_credit=image_credit, "
            "hero_image_width='1200', hero_image_height='630', hero_image_source='primary' WHERE id=?",
            (content_id,),
        )
    if data.featured or data.breaking_flag:  # imagem do hero recalculada ao destacar
        from ..agents.team import compute_hero_image
        compute_hero_image(content_id)
    if data.status == "published" and row["status"] != "published":
        db.execute("UPDATE contents SET published_at = datetime('now') WHERE id = ?", (content_id,))
    elif data.status == "draft" and row["status"] == "published":
        db.execute("UPDATE contents SET published_at = NULL, featured = 0, pinned = 0, "
                   "breaking_flag = 0 WHERE id = ?", (content_id,))
    return _get_or_404("contents", content_id, "Content")


@content_router.delete("/{content_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_content(content_id: int):
    _get_or_404("contents", content_id, "Content")
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
    return _get_or_404("tasks", tid, "Task")


@tasks_router.get("/{task_id}")
def get_task(task_id: int, user: dict = Depends(get_current_user)):
    return _get_or_404("tasks", task_id, "Task")


@tasks_router.patch("/{task_id}")
def update_task(task_id: int, data: TaskUpdate, user: dict = Depends(get_current_user)):
    _get_or_404("tasks", task_id, "Task")
    _update("tasks", task_id, data.model_dump(), touch=True)
    return _get_or_404("tasks", task_id, "Task")


@tasks_router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, user: dict = Depends(get_current_user)):
    _get_or_404("tasks", task_id, "Task")
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
