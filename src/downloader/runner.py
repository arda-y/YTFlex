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
    passed_urls: list[str] | str,
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

    # url's will be collected here
    parsed_links_list = []

    if isinstance(passed_urls, str):
        # check if url is valid
        if not is_valid_url(passed_urls):
            return create_error_response("Invalid URL")

        # check if url is playlist
        if is_playlist(passed_urls):
            return create_error_response(
                "Can't download playlists. Please try again with a single video."
            )
            # this will be re-enabled once i figure out the rest of the code.
            # parsed_links_list = parse_playlist(passed_urls)

        # if not a playlist then it's a single video
        parsed_links_list.append(extract_info(passed_urls))

    elif isinstance(passed_urls, list):
        for video in passed_urls:
            # can't have multiple playlists
            if is_playlist(video):
                return create_error_response(
                    "Can't download multiple playlists. "
                    + "Please try again with a single playlist."
                )
            # check url's are valid
            if not is_valid_url(video):
                # remove invalid url's from list
                passed_urls.remove(video)

        # now we can parse the list
        for video in passed_urls:
            parsed_links_list += extract_info(video)

    # if no urls are valid
    if parsed_links_list == []:
        return create_error_response(
            "Invalid URL(s) passed. " + "Please check your URL(s) and try again."
        )

    # create a list of download info per url
    download_info = []
    for video in parsed_links_list:
        if video is None:
            download_info.append([])
            continue

        # this function will create the required options for yt-dlp
        # regardless of whether the request is for a video or audio file
        # by checking if the request is for a video or audio file internally
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
