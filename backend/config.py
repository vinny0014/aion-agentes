import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv('AION_DB_PATH', str(BASE_DIR / 'database.db'))
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
ALLOWED_ORIGINS = os.getenv('AION_ALLOWED_ORIGINS', '*')

def cors_origins():
    if ALLOWED_ORIGINS.strip() == '*':
        return ['*']
    return [origin.strip() for origin in ALLOWED_ORIGINS.split(',') if origin.strip()]

def allow_credentials():
    return cors_origins() != ['*']
