"""
Utility function to check if a URL is valid.
"""

import requests


def parse_video_id(link: str) -> str | bool:
    """
    Checks if a URL is valid or not, and parses video IDs as well.

    Args:
        link: The URL to check.
    Returns:
        True if the URL is valid, False otherwise.
    """

    if len(link) == 11:
        if (
            requests.head(
                f"https://www.youtube.com/watch?v={link}", timeout=5
            ).status_code
            == 200
        ):
            return link
    else:
        # logic to check if the link is valid, minding www, http, https, etc.
        # returns only the video ID if valid, else False
        if "youtube.com/watch?v=" in link:
            video_id = link.split("youtube.com/watch?v=")[1].split("&")[0]
        elif "youtu.be/" in link:
            video_id = link.split("youtu.be/")[1].split("?")[0]
        else:
            return False  # other formats are not supported for now

        if len(video_id) == 11:
            if (
                requests.head(
                    f"https://www.youtube.com/watch?v={video_id}", timeout=5
                ).status_code
                == 200
            ):
                return video_id

    return False  # catch all failure case
