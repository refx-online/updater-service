from __future__ import annotations

from collections.abc import AsyncIterator
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from aioboto3 import Session
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError

import app.settings as settings

from .base import StorageBackend
from .local import LocalStorageBackend
from .r2 import R2StorageBackend

T = TypeVar("T")


class Storage:
    def __init__(self):
        self._local = LocalStorageBackend(
            root=Path(settings.LOCAL_STORAGE_ROOT),
            public_base_url=settings.STORAGE_PUBLIC_BASE_URL,
        )

        session = Session(
            aws_access_key_id=settings.R2_ACCESS_KEY,
            aws_secret_access_key=settings.R2_SECRET_KEY,
            region_name="auto",
        )

        self._primary: StorageBackend = R2StorageBackend(
            session=session,
            bucket=settings.R2_BUCKET,
            endpoint=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            public_base_url=settings.STORAGE_PUBLIC_BASE_URL,
        )

    async def _with_fallback(
        self,
        fn: Callable[[StorageBackend], T],
    ) -> T:
        try:
            return await fn(self._primary)
        except (BotoCoreError, ClientError, OSError):
            return await fn(self._local)

    async def list_files(self, prefix: str):
        return await self._with_fallback(
            lambda backend: backend.list_files(prefix),
        )

    async def stream_file(self, key: str) -> AsyncIterator[bytes]:
        """Stream file with fallback from primary to local storage."""
        try:
            async for chunk in self._primary.stream_file(key):
                yield chunk
        except (BotoCoreError, ClientError, OSError, FileNotFoundError):
            async for chunk in self._local.stream_file(key):
                yield chunk
