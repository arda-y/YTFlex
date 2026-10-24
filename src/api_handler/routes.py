"""
All API routes for the YTFlex project.
"""

import asyncio
import os

import config
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse

from src.api_handler.app import app, download_rate_limit, get_client_ip, limiter
from src.downloader.runner import download_files

__all__ = ["root", "faq", "audio_download", "video_download"]

# download_files blocks for the whole download, so it runs in a worker thread.
# Calling it directly from an async route would freeze the event loop, and with it
# every other request, until the download ends.
_download_slots = asyncio.Semaphore(config.get("MAX_CONCURRENT_DOWNLOADS", 3))


def _size_limit_mb(client: str) -> int:
    """Size limit in MB: the lower extension limit for client=ext, else the normal limit."""
    api_limit = config.get("MAX_FILE_SIZE")
    if client == "ext":
        return min(config.get("EXT_MAX_FILE_SIZE", api_limit), api_limit)
    return api_limit


async def _run_download(**kwargs):
    """Runs one download in a worker thread, or answers 503 if all slots are busy."""
    if _download_slots.locked():
        return JSONResponse(
            status_code=503,
            content={"message": "The server is busy with other downloads. Try again in a minute."},
        )
    async with _download_slots:
        return await asyncio.to_thread(download_files, **kwargs)


@app.get("/")
async def home():
    """Home route for the API."""
    # Ensure the path points to where your index.html is stored
    # Path.join helps avoid issues between Windows/Linux environments
    # index.html is at root dir, and this file is in src/api_handler, so we go up two levels
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "index.html")

    return FileResponse(file_path)


@app.get("/root")
async def root():
    """To check if the server is running without much hassle."""

    return {"message": "Hello World"}


@app.get("/faq")
async def faq():
    """FAQ page: retention, limits, and data collection policy."""
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "faq.html")

    return FileResponse(file_path)


@app.get("/download/audio")
@limiter.limit(download_rate_limit)
async def audio_download(request: Request, link: str, client: str = "api"):
    """API route for downloading audio files."""

    # bundle the download info
    raw_dl_info = await _run_download(
        passed_url=link,
        is_video_request=False,
        client_ip=get_client_ip(request),
        max_file_size=_size_limit_mb(client),
    )

    return raw_dl_info


@app.get("/download/video")
@limiter.limit(download_rate_limit)
async def video_download(
    request: Request, link: str, res: str | int, mp4: bool = False, client: str = "api"
):
    """API route for downloading video files."""

    raw_dl_info = await _run_download(
        passed_url=link,
        is_video_request=True,
        preferred_res=res,
        convert_to_mp4=mp4,
        client_ip=get_client_ip(request),
        max_file_size=_size_limit_mb(client),
    )

    return raw_dl_info
