from __future__ import annotations

import io
import zipfile

from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

import app.state.services

CLIENT_PREFIX = "resources/client"
PATCHER_PREFIX = "resources/patcher"
LAZER_PREFIX = "resources/lazer"


async def _names(prefix: str) -> set[str]:
    files = await app.state.services.storage.list_files(prefix)
    return {f.name for f in files}


async def download_client_file(filename: str):
    # in-game updater fetches url_full + ".zip" and extracts it
    if filename.endswith(".zip"):
        return await download_zip(CLIENT_PREFIX, filename[:-4])

    # NOTE: stream_file() is lazy so existence has to be checked first,
    # otherwise a missing file dies mid-response (502 through the tunnel).
    if filename not in await _names(CLIENT_PREFIX):
        raise HTTPException(status_code=404, detail="file not found")

    return StreamingResponse(
        app.state.services.storage.stream_file(f"{CLIENT_PREFIX}/{filename}"),
        media_type="application/octet-stream",
    )


async def download_patcher_file(filename: str):
    if filename.endswith(".zip"):
        return await download_zip(PATCHER_PREFIX, filename[:-4])

    if filename not in await _names(PATCHER_PREFIX):
        raise HTTPException(status_code=404, detail="file not found")

    return StreamingResponse(
        app.state.services.storage.stream_file(f"{PATCHER_PREFIX}/{filename}"),
        media_type="application/octet-stream",
    )


async def download_lazer_file(filename: str) -> StreamingResponse:
    # NOTE: deliberately no .zip re-pack here, unlike client/patcher above.
    # ci uploads a real archive, so stream it verbatim -- re-zipping would
    # nest the zip inside another zip.
    if filename not in await _names(LAZER_PREFIX):
        raise HTTPException(status_code=404, detail="file not found")

    return StreamingResponse(
        app.state.services.storage.stream_file(f"{LAZER_PREFIX}/{filename}"),
        media_type="application/octet-stream",
    )


async def get_lazer_metadata() -> StreamingResponse:
    # ci writes latest.json next to the archive on every publish. 404 until the
    # first build lands, which is honest -- an empty manifest would read as
    # "up to date" and silently skip the update.
    if "latest.json" not in await _names(LAZER_PREFIX):
        raise HTTPException(status_code=404, detail="no lazer build published yet")

    return StreamingResponse(
        app.state.services.storage.stream_file(f"{LAZER_PREFIX}/latest.json"),
        media_type="application/json",
    )


async def download_zip(prefix: str, filename: str):
    if filename not in await _names(prefix):
        raise HTTPException(status_code=404, detail="file not found")

    raw = b"".join(
        [
            chunk
            async for chunk in app.state.services.storage.stream_file(f"{prefix}/{filename}")
        ]
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, raw)

    # `no-store`, deliberately.
    #
    # `/resources/client/` is served from fixed filenames that CI overwrites in
    # place, so an edge cache hit here is always wrong: a new build publishes to
    # the same URL, and a cached zip hands the client last week's bytes. The
    # symptom is nasty because it looks healthy -- the client logs only that it
    # downloaded a file successfully, and then re-downloads the entire set on
    # every check because the hash never matches what `metadata.json` advertises.
    #
    # The reason it happened: this returned a buffered `Response`, which is
    # cacheable by default, while the raw-file path below returns a lazy
    # `StreamingResponse` with no validator and was never cached. So only `.zip`
    # got cached, for Cloudflare's default extension TTL (max-age=14400). The
    # origin simply never expressed an opinion.
    #
    # Caching eligibility is a property of the **URL being immutable**, not of the
    # file extension. `latest.json` points at `osu-lazer-<sha1>.zip`, so the lazer
    # path is content-addressed and must stay cacheable -- which is why
    # `download_lazer_file` above is deliberately left alone.
    return Response(
        buf.getvalue(),
        media_type="application/zip",
        headers={"Cache-Control": "no-store"},
    )
