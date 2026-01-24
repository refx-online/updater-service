from __future__ import annotations

from fastapi.responses import StreamingResponse

import app.state.services

AVATAR_PREFIX = "resources/ava"
EXTS = ["png", "jpg", "jpeg", "gif"]


async def get_avatar(id: int):
    for ext in EXTS:
        stream = app.state.services.storage.stream_file(f"{AVATAR_PREFIX}/{id}.{ext}")
        return StreamingResponse(
            stream,
            media_type=f"image/{ext}",
        )

    return StreamingResponse(
        app.state.services.storage.stream_file(f"{AVATAR_PREFIX}/default.jpg"),
        media_type="image/jpeg",
    )
