"""
Utility function to create a response object for the client.
"""

import math
import os


def create_response(
    cdn_link: str,
    thumbnail: str,
    filename: str,
    duration: int,
    filesize: int,
):
    """
    Creates and returns a response object for the client.

    Args:
        resolution: the resolution of the file, if it's audio, it'll be None
        link: the download link of the file
        title: the title of the file
        thumbnail: the thumbnail of the file
        duration: the duration of the file
        filename: the filename of the file
    """

    def convert_size(size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    readable_filesize = convert_size(filesize)

    readable_duration = (
        f"{duration // 3600}h {(duration % 3600) // 60}m {duration % 60}s"
    )

    if readable_duration.startswith("0h "):
        readable_duration = readable_duration[3:]
    if readable_duration.startswith("0m "):
        readable_duration = readable_duration[3:]
    if readable_duration.startswith("0s"):
        readable_duration = readable_duration[3:]

    response = [
        {
            "link": cdn_link,
            "message": "File downloaded successfully",
            "metadata": {
                "title": filename.split(".")[0],
                "duration": readable_duration,
                "thumbnail": thumbnail,
                "filesize": readable_filesize,
                "filename": filename,
                "extension": os.path.splitext(filename)[1],
            },
        }
    ]

    return response


def create_error_response(message: str) -> dict:
    """
    Creates a response with error message.

    Args:
        error: The error message.

    Returns:
        A dictionary containing the error message.
    """

    # responses = {
    #     "invalidurl": "Invalid URL/ID provided",
    #     "unavailable": "Video is not accessible in our server location",
    #     "file_too_big": "Video is too big to download",
    #     "resolution_unavailable": "Requested resolution is not available for the video",
    #     "invalid_resolution": "Invalid resolution provided",
    # }
    # this will be put to use in the following commit(s), pinky promise

    return {"message": message}
