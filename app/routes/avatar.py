from __future__ import annotations

import logging

from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError
from fastapi import Response
from fastapi.responses import StreamingResponse

import app.state.services

log = logging.getLogger(__name__)

AVATAR_PREFIX = "resources/ava"
EXTS = ["png", "jpg", "jpeg", "gif"]

# storage errors that mean "can't list right now" (r2 down, creds bad,
# disk gone). anything else propagates as 5xx so it actually gets noticed.
LIST_ERRORS = (BotoCoreError, ClientError, OSError)


async def get_avatar(id: int):
    # NOTE: stream_file() is a lazy async generator — calling it never
    # raises, so the old code returned 200 with a truncated empty body for
    # missing files instead of falling through to the default. probe
    # existence first via list_files() (works on r2 + local backends).
    try:
        names = {n async for n in _iter_names()}
    except LIST_ERRORS as e:
        log.warning("avatar listing failed, serving 404: %r", e)
        names = set()

    for ext in EXTS:
        if f"{id}.{ext}" in names:
            return StreamingResponse(
                app.state.services.storage.stream_file(f"{AVATAR_PREFIX}/{id}.{ext}"),
                media_type=f"image/{ext}",
            )

    for ext in EXTS:
        if f"default.{ext}" in names:
            return StreamingResponse(
                app.state.services.storage.stream_file(f"{AVATAR_PREFIX}/default.{ext}"),
                media_type=f"image/{ext}",
            )

    return Response(status_code=404)


async def _iter_names():
    for meta in await app.state.services.storage.list_files(AVATAR_PREFIX):
        yield meta.name
