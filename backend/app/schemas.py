"""Schemas Pydantic — contratos da API REST."""
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


# ---------- Users ----------
class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: int
    created_at: str


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = Field(default=None, pattern="^(user|admin)$")
    is_active: int | None = Field(default=None, ge=0, le=1)


# ---------- Agents ----------
class AgentIn(BaseModel):
    slug: str = Field(min_length=2, max_length=60, pattern="^[a-z0-9-]+$")
    name: str
    role: str
    description: str = ""
    status: str = Field(default="idle", pattern="^(idle|running|blocked|error)$")
    config_json: str = "{}"


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(idle|running|blocked|error)$")
    config_json: str | None = None


# ---------- Content ----------
class ContentIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(min_length=3, max_length=200, pattern="^[a-z0-9-]+$")
    body: str = ""
    excerpt: str = ""
    status: str = Field(default="draft", pattern="^(draft|queued|published)$")
    agent_id: int | None = None
    seo_title: str = ""
    seo_description: str = ""
    category: str = ""
    tags: str = ""  # separadas por vírgula


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    excerpt: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|queued|published)$")
    seo_title: str | None = None
    seo_description: str | None = None
    category: str | None = None
    tags: str | None = None


# ---------- Tasks ----------
class TaskIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = ""
    status: str = Field(default="todo", pattern="^(todo|doing|done|blocked)$")
    priority: int = Field(default=3, ge=1, le=5)
    agent_id: int | None = None
    assignee_id: int | None = None
    due_at: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(todo|doing|done|blocked)$")
    priority: int | None = Field(default=None, ge=1, le=5)
    agent_id: int | None = None
    assignee_id: int | None = None
    due_at: str | None = None


# ---------- Logs ----------
class LogIn(BaseModel):
    level: str = Field(default="info", pattern="^(info|warn|error)$")
    source: str = "system"
    message: str
    meta_json: str = "{}"


# ---------- Memory ----------
class MemoryIn(BaseModel):
    scope: str = "global"
    key: str = Field(min_length=1, max_length=200)
    value: str


# ---------- Settings ----------
class SettingIn(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: str


# ---------- Content Queue ----------
class QueueIn(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    provider: str = Field(default="pending", pattern="^(pending|openai|anthropic|openrouter|gemini)$")
    template: str = "artigo_padrao"
    scheduled_for: str | None = None


# ---------- Contato (público) ----------
class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    message: str = Field(min_length=5, max_length=3000)
