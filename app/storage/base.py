from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(slots=True)
class FileMeta:
    name: str
    size: int
    md5: str
    url: str


class StorageBackend(ABC):
    @abstractmethod
    async def list_files(self, prefix: str) -> list[FileMeta]: ...

    @abstractmethod
    async def stream_file(self, key: str) -> AsyncIterator[bytes]: ...
