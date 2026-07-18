"""Authentication routes: registration, login, token rotation and profile."""
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..core import database as db
from ..core.config import settings
from ..core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    rotate_refresh_token,
    verify_password,
)
from ..schemas import RefreshIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn):
    if db.query_one("SELECT id FROM users WHERE email = ?", (data.email,)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")
    role = "user"
    if data.setup_token:
        if not settings.ADMIN_SETUP_TOKEN or not secrets.compare_digest(
                data.setup_token, settings.ADMIN_SETUP_TOKEN):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid admin setup token")
        if db.query_one("SELECT id FROM users WHERE role='admin' LIMIT 1"):
            raise HTTPException(status.HTTP_409_CONFLICT, "An administrator already exists")
        role = "admin"
    uid = db.execute(
        "INSERT INTO users (email, name, password_hash, role) VALUES (?, ?, ?, ?)",
        (data.email, data.name, hash_password(data.password), role),
    )
    db.execute(
        "INSERT INTO logs (level, source, message) VALUES ('info', 'auth', ?)",
        (f"New user registered: {data.email} ({role})",),
    )
    return db.query_one(
        "SELECT id, email, name, role, is_active, created_at FROM users WHERE id = ?", (uid,)
    )


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = db.query_one("SELECT * FROM users WHERE email = ?", (form.username,))
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user["is_active"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return TokenOut(
        access_token=create_access_token(user["id"], user["role"]),
        refresh_token=create_refresh_token(user["id"]),
    )


@router.post("/refresh", response_model=TokenOut)
def refresh(data: RefreshIn):
    return rotate_refresh_token(data.refresh_token)


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return user
