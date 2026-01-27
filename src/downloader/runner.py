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
from yt_dlp import YoutubeDL
from src.downloader.utils.base import *


def download_files(
    passed_url: str,
    is_video_request: bool,
    preferred_res: int = 720,
    convert_to_mp4: bool = False,
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

        preferred_res: The preferred resolution to download. Defaults to 720p.
        If not available, audio will be downloaded instead.

        convert_to_mp4: Whether to convert the downloaded file to mp4 or not. Defaults to False.
        Will have no effect if downloading audio only.
    """

    # check if url is valid
    link = parse_video_id(passed_url)

    if not link:
        return create_error_response(
            "Invalid URL passed. Please check your URL and try again."
        )

    download_info = []
    video = extract_info(link)

    ydl_opts = ydl_opts_builder(
        video.title, is_video_request, preferred_res, convert_to_mp4
    )

    # create a download object
    filename_collector = FilenameCollectorPP()
    ydl = YoutubeDL(ydl_opts)
    ydl.add_post_processor(filename_collector)
    ydl.download([video.url])
    last_downloaded_dir: str = filename_collector.filenames[-1]
    filename: str = os.path.basename(last_downloaded_dir)
    filedir: str = os.path.dirname(last_downloaded_dir)
    cdn_link: str = create_download_link(filedir, filename)
    download_info.append(
        create_response(cdn_link, video.thumbnail, filename, video.duration, False)
    )
    return download_info
