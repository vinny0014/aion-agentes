"""Schemas Pydantic — contratos da API REST."""
from urllib.parse import urlparse

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------- Auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    setup_token: str = Field(default="", max_length=256)

    @field_validator("password")
    @classmethod
    def bcrypt_length_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


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
    seo_title: str = Field(default="", max_length=60)
    seo_description: str = Field(default="", max_length=160)
    category: str = ""
    tags: str = ""  # comma separated
    author: str = "AION Editorial"
    image_url: str = ""
    image_alt: str = ""
    featured: int = 0
    pinned: int = 0
    breaking_flag: int = 0
    editors_pick: int = 0
    scheduled_at: str = ""
    source_url: str = ""

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        if value and urlparse(value).scheme not in {"http", "https"}:
            raise ValueError("Source URL must use HTTP or HTTPS")
        return value


class ContentUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    image_url: str | None = None
    image_alt: str | None = None
    featured: int | None = None
    pinned: int | None = None
    breaking_flag: int | None = None
    editors_pick: int | None = None
    scheduled_at: str | None = None
    source_url: str | None = None
    body: str | None = None
    excerpt: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|queued|published)$")
    seo_title: str | None = Field(default=None, max_length=60)
    seo_description: str | None = Field(default=None, max_length=160)
    category: str | None = None
    tags: str | None = None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        if value and urlparse(value).scheme not in {"http", "https"}:
            raise ValueError("Source URL must use HTTP or HTTPS")
        return value


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


class EmailIn(BaseModel):
    email: EmailStr
