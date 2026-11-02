"""
All API routes for the YTFlex project.
"""

import asyncio
import os
import re
from pathlib import Path
from urllib.parse import quote

import config
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, Response

from src.api_handler.app import app, download_rate_limit, get_client_ip, limiter
from src.downloader.runner import download_files
from src.downloader.utils import progress

__all__ = [
    "root",
    "faq",
    "gone",
    "download_progress",
    "userscript",
    "audio_download",
    "video_download",
    "slug_download",
]

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
            content={
                "message": "The server is busy with other downloads. Try again in a minute."
            },
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


@app.get("/gone")
async def gone():
    """Shown by nginx (error_page on the cdn download location) when a requested file no longer exists."""
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "gone.html")

    return FileResponse(
        file_path, status_code=404, headers={"Cache-Control": "no-store"}
    )


@app.get("/ytflex.user.js")
async def userscript():
    """The browser userscript. Served from the repo copy, so it cannot drift from the source."""
    file_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "userscript", "ytflex-send.user.js"
    )

    return FileResponse(file_path, media_type="text/javascript; charset=utf-8")


@app.get("/progress/{progress_id}")
async def download_progress(progress_id: str):
    """Progress of a running download: {"stage": ..., "percent": 0-100}. 404 if unknown or expired."""
    entry = progress.get(progress_id) if progress.valid_id(progress_id) else None
    if entry is None:
        return JSONResponse(status_code=404, content={"message": "No such download."})

    return JSONResponse(entry, headers={"Cache-Control": "no-store"})


@app.get("/download/audio")
@limiter.limit(download_rate_limit)
async def audio_download(
    request: Request, link: str, client: str = "api", progress_id: str | None = None
):
    """API route for downloading audio files."""

    # bundle the download info
    raw_dl_info = await _run_download(
        passed_url=link,
        is_video_request=False,
        client_ip=get_client_ip(request),
        max_file_size=_size_limit_mb(client),
        client=client,
        progress_id=progress_id if progress.valid_id(progress_id) else None,
    )

    return raw_dl_info


@app.get("/download/video")
@limiter.limit(download_rate_limit)
async def video_download(
    request: Request,
    link: str,
    res: str | int,
    mp4: bool = False,
    client: str = "api",
    progress_id: str | None = None,
):
    """API route for downloading video files."""

    raw_dl_info = await _run_download(
        passed_url=link,
        is_video_request=True,
        preferred_res=res,
        convert_to_mp4=mp4,
        client_ip=get_client_ip(request),
        max_file_size=_size_limit_mb(client),
        client=client,
        progress_id=progress_id if progress.valid_id(progress_id) else None,
    )

    return raw_dl_info


SLUG_RE = re.compile(r"^[a-z0-9]{20}$")
DOWNLOAD_ROOT = Path("./mountpoint/downloads").resolve()


def _slug_file(slug: str) -> Path | None:
    """The one file stored for this slug, or None if the slug is malformed, unknown or expired."""
    if not SLUG_RE.match(slug):
        return None
    try:
        return next(
            (p for p in sorted((DOWNLOAD_ROOT / slug).iterdir()) if p.is_file()), None
        )
    except OSError:
        return None


@app.get("/{slug}")
async def slug_download(slug: str):
    """Public link <site>/ytflex/<slug>. The app only looks the slug up and answers with an
    X-Accel-Redirect to the internal file location (nginx then streams the file itself, with
    ranges/resume) plus the Content-Disposition that restores the real filename. Unknown,
    expired and never-existing slugs all get the gone page. Keep this route last: it matches
    any single path segment."""
    file_path = _slug_file(slug)
    if file_path is None:
        return await gone()
    name = file_path.name
    ascii_name = re.sub(r'[^\x20-\x7e]|["\\]', "_", name)
    return Response(
        status_code=200,
        headers={
            "X-Accel-Redirect": f"/_ytflex_files/{slug}/{quote(name)}",
            "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}",
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
        },
    )
