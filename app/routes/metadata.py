from __future__ import annotations

from fastapi.responses import JSONResponse

import app.state.services

CLIENT_PREFIX = "resources/client"
PATCHER_PREFIX = "resources/patcher"


async def get_client_metadata():
    files = await app.state.services.storage.list_files(CLIENT_PREFIX)

    return JSONResponse(
        [
            {
                "filename": f.name,
                "file_hashmd5": f.md5,
                "file_size": f.size,
                "url_full": f.url,
            }
            for f in files
        ],
    )


async def get_patcher_metadata():
    files = await app.state.services.storage.list_files(PATCHER_PREFIX)

    # yeah old format was cursed, but we keep compatibility
    return JSONResponse(
        {
            f.name: {
                "url": f.url,
                "hash_md5": f.md5,
                "size": f.size,
            }
            for f in files
        },
    )
