from __future__ import annotations

from fastapi import APIRouter
from fastapi import Response

from . import metadata
from . import stream

router = APIRouter(
    default_response_class=Response,
    tags=["Updater"],
)

router.add_api_route(
    "/metadata.json",
    metadata.get_client_metadata,
    methods=["GET"],
)

router.add_api_route(
    "/patcher",
    metadata.get_patcher_metadata,
    methods=["GET"],
)

router.add_api_route(
    "/files/{filename}",
    stream.download_client_file,
    methods=["GET"],
)

router.add_api_route(
    "/patcher/{filename}",
    stream.download_patcher_file,
    methods=["GET"],
)
