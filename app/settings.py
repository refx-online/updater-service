from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def read_bool(value: str) -> bool:
    return value.lower() in ("true", "1")


def getenv(name: str, default: str | None = None) -> str:
    # NOTE: plain os.environ[name] dies with a bare KeyError at import time,
    # which tells you nothing. fail fast with the actual var name instead.
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"missing required env var: {name}")
    return value


DEBUG = read_bool(getenv("DEBUG", "false"))
HOST = getenv("HOST", "0.0.0.0")
PORT = int(getenv("PORT", "1272"))

STORAGE_PUBLIC_BASE_URL = getenv("STORAGE_PUBLIC_BASE_URL", "")

R2_ACCOUNT_ID = getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY = getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY = getenv("R2_SECRET_KEY", "")
R2_BUCKET = getenv("R2_BUCKET", "")

LOCAL_STORAGE_ROOT = getenv("LOCAL_STORAGE_ROOT", "")

# bearer token for POST /resources/{client,patcher}/{filename} uploads.
# empty = uploads disabled.
UPLOAD_TOKEN = getenv("UPLOAD_TOKEN", "")
