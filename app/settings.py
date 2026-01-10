from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def read_bool(value: str) -> bool:
    return value.lower() in ("true", "1")


DEBUG = read_bool(os.environ["DEBUG"])
HOST = os.environ["HOST"]
PORT = int(os.environ["PORT"])

STORAGE_PUBLIC_BASE_URL = os.environ["STORAGE_PUBLIC_BASE_URL"]

R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY = os.environ["R2_ACCESS_KEY"]
R2_SECRET_KEY = os.environ["R2_SECRET_KEY"]
R2_BUCKET = os.environ["R2_BUCKET"]

LOCAL_STORAGE_ROOT = os.environ["LOCAL_STORAGE_ROOT"]
