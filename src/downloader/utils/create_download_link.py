"""
Utility function to create a download link for a file.
"""

from urllib.parse import quote
import os
import random
import config

SLUG_LEN = 20


def create_download_link(filedir: str, filename: str) -> str:
    """
    Creates a download link for the file
    (the random folder name doubles as the public slug)
    Args:
        filename: FULL filename of the file, including the extension
    """

    ip_or_domain = os.getenv("ip_or_domain", config.get("IP_OR_DOMAIN"))
    cdn_location = os.getenv("cdn_location", config.get("CDN_LOCATION"))

    random_string = "".join(
        random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=SLUG_LEN)
    )
    os.makedirs(
        os.path.join(filedir, random_string), exist_ok=True
    )  # create random folder to store file inside

    os.rename(
        os.path.join(filedir, filename), os.path.join(filedir, random_string, filename)
    )  # move file into the random folder we just created

    # The filename stays out of the URL: the app finds the file by slug and the
    # Content-Disposition header restores the name on download.
    return f"{ip_or_domain}/{quote(cdn_location)}/{quote(random_string)}"
