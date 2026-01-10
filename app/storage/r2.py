from __future__ import annotations

from collections.abc import AsyncIterator

from aioboto3 import Session

from .base import FileMeta
from .base import StorageBackend


class R2StorageBackend(StorageBackend):
    def __init__(
        self,
        *,
        session: Session,
        bucket: str,
        endpoint: str,
        public_base_url: str,
    ):
        self._session = session
        self._bucket = bucket
        self._endpoint = endpoint
        self._base_url = public_base_url.rstrip("/")

    def _client(self):
        return self._session.client("s3", endpoint_url=self._endpoint)

    async def list_files(self, prefix: str) -> list[FileMeta]:
        files: list[FileMeta] = []

        async with self._client() as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    name = obj["Key"].split("/")[-1]
                    if not name:
                        continue

                    # etag is md5 for singlepart uploads, but for multipart
                    # uploads its in format "hash-n" where n is the number of parts
                    # but we can be 99% sure that im not using multipart.
                    etag = obj["ETag"].strip('"')

                    # for multipart, i cant guarantee its a valid md5
                    if "-" in etag:
                        # TODO: should i hash this correctly?
                        md5 = etag
                    else:
                        # singlepart upload, etag is the md5 hash
                        md5 = etag

                    files.append(
                        FileMeta(
                            name=name,
                            size=obj["Size"],
                            md5=md5,
                            url=f"{self._base_url}/{prefix}/{name}",
                        ),
                    )

        return files

    async def stream_file(self, key: str) -> AsyncIterator[bytes]:
        async with self._client() as s3:
            obj = await s3.get_object(Bucket=self._bucket, Key=key)
            async for chunk in obj["Body"].iter_chunks():
                yield chunk
