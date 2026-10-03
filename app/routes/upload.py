from __future__ import annotations

import hmac
from pathlib import Path

from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse

import app.settings as settings

ALLOWED_PREFIXES = ("client", "patcher", "lazer")


async def upload_file(prefix: str, filename: str, request: Request, authorization: str = Header(default="")):
    # NOTE: uploads always go to local disk, even if r2 is configured —
    # the ci pipeline pushes here and local is the fallback source anyway.
    if not settings.UPLOAD_TOKEN or not settings.LOCAL_STORAGE_ROOT:
        raise HTTPException(status_code=503, detail="uploads disabled")

    if prefix not in ALLOWED_PREFIXES:
        raise HTTPException(status_code=404, detail="unknown prefix")

    # path params can't contain slashes, but be explicit anyway
    if not filename or "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="bad filename")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token, settings.UPLOAD_TOKEN):
        raise HTTPException(status_code=401, detail="bad token")

    dest = Path(settings.LOCAL_STORAGE_ROOT) / "resources" / prefix / filename
    dest.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    with open(dest, "wb") as f:
        async for chunk in request.stream():
            f.write(chunk)
            size += len(chunk)

    return JSONResponse({"filename": filename, "size": size})
