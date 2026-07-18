"""Segurança — hash de senha (bcrypt), JWT de acesso e refresh tokens."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

from . import database as db
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError, UnicodeError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expires.isoformat()),
    )
    return raw


def rotate_refresh_token(raw: str) -> dict:
    """Valida, revoga e emite novo par de tokens."""
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    row = db.query_one(
        "SELECT * FROM refresh_tokens WHERE token_hash = ? AND revoked = 0", (token_hash,)
    )
    if not row or datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    db.execute("UPDATE refresh_tokens SET revoked = 1 WHERE id = ?", (row["id"],))
    user = db.query_one("SELECT * FROM users WHERE id = ? AND is_active = 1", (row["user_id"],))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive user")
    return {
        "access_token": create_access_token(user["id"], user["role"]),
        "refresh_token": create_refresh_token(user["id"]),
        "token_type": "bearer",
    }


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    cred_exc = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Invalid credentials", {"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise cred_exc
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise cred_exc
    user = db.query_one(
        "SELECT id, email, name, role, is_active, created_at FROM users WHERE id = ?", (user_id,)
    )
    if not user or not user["is_active"]:
        raise cred_exc
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator access required")
    return user
