from __future__ import annotations

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

import app.state.services

CLIENT_PREFIX = "resources/client"
PATCHER_PREFIX = "resources/patcher"


async def download_client_file(filename: str):
    try:
        stream = app.state.services.storage.stream_file(f"{CLIENT_PREFIX}/{filename}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file not found")

    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
    )


async def download_patcher_file(filename: str):
    try:
        stream = app.state.services.storage.stream_file(f"{PATCHER_PREFIX}/{filename}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file not found")

    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
    )
