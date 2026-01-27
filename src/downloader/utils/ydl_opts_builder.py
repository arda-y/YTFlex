"""
Utility function to build the options for yt-dlp.
"""

import os
import config
from src.downloader.utils.find_appropriate_res import find_appropriate_res


def ydl_opts_builder(
    title: str,
    is_video_request: bool,
    preferred_res: int = 720,
    convert_to_mp4: bool = False,
):
    """
    Utility function for building the options for yt-dlp.

    Args:
        title: The title of the file to download.

        is_video_request: Whether the request is for a video or audio file.

        preferred_res: The preferred resolution to download. Defaults to 720p.
        Not used if downloading audio only.

        convert_to_mp4: Whether to convert the downloaded file to mp4 or not. Defaults to False.
        Will have no effect if downloading audio only.
    """

    download_path = "./mountpoint/downloads"
    max_file_size = config.get("MAX_FILE_SIZE")
    show_yt_dlp_output = config.get("SHOW_YT_DLP_OUTPUT")

    if is_video_request:
        # format string for yt-dlp
        preferred_res = find_appropriate_res(preferred_res)

        ydl_opts = {
            "format": f"bestvideo[height<={preferred_res}][filesize<{max_file_size}M]+"
            + f"bestaudio/best[height<={preferred_res}][filesize<{int(max_file_size/4)}M]",
            "outtmpl": os.path.join(download_path, f"{title}-%(height)sp.%(ext)s"),
            "windowsfilenames": True,
            "quiet": not show_yt_dlp_output,
        }

        if convert_to_mp4:
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
            ]

    else:
        ydl_opts = {
            "format": f"bestaudio/best[filesize<{int(max_file_size)}M]",
            "outtmpl": os.path.join(download_path, f"{title}"),
            "windowsfilenames": True,
            "quiet": not show_yt_dlp_output,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

    return ydl_opts
