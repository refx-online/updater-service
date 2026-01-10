from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator
from pathlib import Path

from .base import FileMeta
from .base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, *, root: Path, public_base_url: str):
        self._root = root
        self._base_url = public_base_url.rstrip("/")

    async def _compute_md5(self, file_path: Path) -> str:
        def _hash_file():
            md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    md5.update(chunk)
            return md5.hexdigest()

        return await asyncio.to_thread(_hash_file)

    async def list_files(self, prefix: str) -> list[FileMeta]:
        base = self._root / prefix
        if not base.exists() or not base.is_dir():
            return []

        out: list[FileMeta] = []

        def _list_dir():
            return [f for f in base.iterdir() if f.is_file()]

        files = await asyncio.to_thread(_list_dir)

        tasks = []
        for file in files:
            # todo: CACHE IT!!!!
            #       its 02:04 am right now i need to sleep..
            tasks.append(self._compute_md5(file))

        md5_hashes = await asyncio.gather(*tasks)

        for file, md5 in zip(files, md5_hashes):
            out.append(
                FileMeta(
                    name=file.name,
                    size=file.stat().st_size,
                    md5=md5,
                    url=f"{self._base_url}/{prefix}/{file.name}",
                ),
            )

        return out

    async def stream_file(self, key: str) -> AsyncIterator[bytes]:
        file_path = self._root / key

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        def _read_chunk(f):
            return f.read(8192)

        with open(file_path, "rb") as f:
            while True:
                chunk = await asyncio.to_thread(_read_chunk, f)
                if not chunk:
                    break
                yield chunk
