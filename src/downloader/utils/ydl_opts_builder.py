"""
Utility function to build the options for yt-dlp.
"""

import os
import config


def ydl_opts_builder(
    title: str,
    is_video_request: bool,
    preferred_res: str = "720",
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
        preferred_res = parse_requested_resolution(preferred_res)

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


def parse_requested_resolution(requested_res: int | str):
    """
    Sanitizes the requested resolution, ensuring it is within acceptable bounds.

    Also attempts to convert the passed resolution to an integer if it is a string.

    Args:
        preferred_res: The preferred resolution to download.
        Accepts both int and str types, and "max"/"best" keywords.
    """

    max_res: int = config.get("MAX_RES")

    if isinstance(requested_res, str):

        if requested_res in ["max", "maximum", "best", "highest"]:
            return max_res

        if requested_res.isdigit():
            requested_res = int(requested_res)
        else:
            try:
                requested_res = int(requested_res.replace("p", ""))
            except ValueError:
                return None

    # at this point, requested_res is definitely an int
    if not isinstance(requested_res, int):
        return None

    if requested_res >= max_res:
        return max_res

    if requested_res < 0:
        return None

    return requested_res
