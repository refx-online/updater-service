from __future__ import annotations

from fastapi import APIRouter
from fastapi import Response

from . import avatar
from . import metadata
from . import stream
from . import upload

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

# hi??? merge pls???
router.add_api_route(
    "/resources/client/{filename}",
    stream.download_client_file,
    methods=["GET"],
)

router.add_api_route(
    "/resources/patcher/{filename}",
    stream.download_patcher_file,
    methods=["GET"],
)

router.add_api_route(
    "/resources/{prefix}/{filename}",
    upload.upload_file,
    methods=["POST"],
)

# todo: move to assets-service
router.add_api_route(
    "/{id}",
    avatar.get_avatar,
    methods=["GET"],
)
