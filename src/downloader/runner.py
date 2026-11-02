"""
The head file of all utility functions. This file will be imported by the API handler.
Will contain all logic involved in downloading files by either importing from other files or
by having the logic here.
"""

# pylint: disable=too-many-branches
#
# this file is the main file for the downloader module
# and it requires too many branches to be reduced into a sane number
# so we disable the warning for this file only

# pylint: disable=wildcard-import
#
# the wildcard import is used to import all utility functions which are
# going to be used in this file.

# pylint: disable=fixme
#
# this is for pylint to not fail the build because of the fixme comments


import os
import threading
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from src.downloader.utils.base import *
from src.downloader.utils import progress
from src.db_handler.bandwidth import record_download

DOWNLOAD_ROOT = Path("./mountpoint/downloads").resolve()

# Downloads run in worker threads, so several can be active at once. yt-dlp writes
# to a shared folder under the video title until create_download_link moves the file
# into its own random folder. Two requests with the same title and type must not
# overlap in that window, so each (title, type) pair gets its own lock.
_title_locks: dict[tuple[str, bool], threading.Lock] = {}
_title_locks_guard = threading.Lock()


def _title_lock(title: str, is_video_request: bool) -> threading.Lock:
    """Returns the lock for this (title, type) pair, creating it on first use."""
    with _title_locks_guard:
        return _title_locks.setdefault((title, is_video_request), threading.Lock())


def download_files(
    passed_url: str,
    is_video_request: bool,
    preferred_res: str = "1080",
    convert_to_mp4: bool = False,
    client_ip: str | None = None,
    max_file_size: int | None = None,
    client: str = "other",
    progress_id: str | None = None,
):
    """
    Downloads files from youtube using yt-dlp.
    If a preferred resolution is given, it will attempt to download that resolution.
    If the preferred resolution is not available, it will download the next best resolution.
    If no preferred resolution is given, it will download audio only instead.

    Args:
        passed_urls: List of urls to download, or a single url as a string.
        Incompatible with multiple playlists.

        is_video_request: Whether the request is for a video or audio file.

        preferred_res: The preferred resolution to download. Defaults to 1080p.
        If not available, audio will be downloaded instead.

        convert_to_mp4: Whether to convert the downloaded file to mp4 or not. Defaults to False.
        Will have no effect if downloading audio only.

        max_file_size: File size limit in MB. Defaults to MAX_FILE_SIZE from config.yaml.

        client: Kind of caller ("ext" for the browser extension), stored with the download record.

        progress_id: Optional id the caller polls through GET /progress/{id}.
    """

    if progress_id:
        progress.update(progress_id, stage="preparing", percent=0)

    # check if url is valid
    print(f"Checking URL: {passed_url}")
    link = parse_video_id(passed_url)
    print(f"Parsed link: {link}")

    if not link:
        return create_error_response(
            "Invalid URL passed. Please check your URL and try again."
        )

    download_info = []
    video = extract_info(link)

    if video is None:
        return create_error_response(
            "Video is unavailable. Please check your URL and try again."
        )

    ydl_opts = ydl_opts_builder(
        video.title, is_video_request, preferred_res, convert_to_mp4, max_file_size
    )

    with _title_lock(video.title, is_video_request):
        return _download_and_respond(
            link, video, ydl_opts, client_ip, download_info, client, progress_id
        )


def _download_and_respond(
    link, video, ydl_opts, client_ip, download_info, client, progress_id=None
):
    """Runs yt-dlp and builds the response. The caller holds the title lock."""

    # create a download object
    filename_collector = FilenameCollectorPP()
    ydl = YoutubeDL(ydl_opts)
    ydl.add_post_processor(filename_collector)
    if progress_id:
        download_hook, pp_hook = progress.make_hooks(progress_id)
        ydl.add_progress_hook(download_hook)
        ydl.add_postprocessor_hook(pp_hook)
    try:
        ydl.download([f"https://www.youtube.com/watch?v={link}"])
    except DownloadError:
        return create_error_response(
            "Download failed. The video may be unavailable, or no version fits the size limit."
        )
    last_downloaded_dir: str = filename_collector.filenames[-1]

    # Containment check: confirm yt-dlp actually wrote inside DOWNLOAD_ROOT.
    # Title sanitization (see extract_metadata.py) is the primary defense against
    # a crafted video title escaping the download folder; this is the backstop
    # in case that sanitization is ever weakened, bypassed, or a future edit
    # removes it without the reviewer noticing this line.
    resolved_path = Path(last_downloaded_dir).resolve()
    if DOWNLOAD_ROOT not in resolved_path.parents:
        try:
            os.remove(last_downloaded_dir)
        except OSError:
            pass
        return create_error_response(
            "Download rejected: resulting file path was outside the allowed directory."
        )

    file_size = os.path.getsize(last_downloaded_dir)

    # Historical bandwidth dataset - see src/db_handler/bandwidth.py for the
    # 7-day IP-scrub retention behavior. Never let a logging failure break
    # an otherwise-successful download.
    if client_ip:
        try:
            record_download(client_ip, file_size, client)
        except Exception:  # pylint: disable=broad-except
            pass

    filename: str = os.path.basename(last_downloaded_dir)
    filedir: str = os.path.dirname(last_downloaded_dir)
    cdn_link: str = create_download_link(filedir, filename)
    download_info.append(
        create_response(cdn_link, video.thumbnail, filename, video.duration, file_size)
    )
    return download_info
