from __future__ import annotations

import logging
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

log = logging.getLogger(__name__)

T = TypeVar("T")

# errors that mean "r2 didn't work, try local". ValueError covers
# aioboto3's "Invalid endpoint" when creds are missing/malformed.
R2_ERRORS = (BotoCoreError, ClientError, OSError, ValueError)


class Storage:
    def __init__(self):
        self._local = LocalStorageBackend(
            root=Path(settings.LOCAL_STORAGE_ROOT),
            public_base_url=settings.STORAGE_PUBLIC_BASE_URL,
        )

        # NOTE: no point ever touching r2 without an account + bucket —
        # go straight local instead of failing into the fallback per call.
        self._use_r2 = bool(settings.R2_ACCOUNT_ID and settings.R2_BUCKET)

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
        if not self._use_r2:
            return await fn(self._local)
        try:
            return await fn(self._primary)
        except R2_ERRORS as e:
            log.warning("r2 failed, falling back to local: %r", e)
            return await fn(self._local)

    async def list_files(self, prefix: str):
        return await self._with_fallback(
            lambda backend: backend.list_files(prefix),
        )

    async def stream_file(self, key: str) -> AsyncIterator[bytes]:
        """Stream file with fallback from primary to local storage."""
        if not self._use_r2:
            async for chunk in self._local.stream_file(key):
                yield chunk
            return
        try:
            async for chunk in self._primary.stream_file(key):
                yield chunk
        except R2_ERRORS as e:
            log.warning("r2 failed, falling back to local: %r", e)
            async for chunk in self._local.stream_file(key):
                yield chunk
