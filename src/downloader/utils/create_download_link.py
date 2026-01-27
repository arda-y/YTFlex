"""
Utility function to create a download link for a file.
"""

from urllib.parse import quote
import os
import random
import config


def create_download_link(filedir: str, filename: str) -> str:
    """
    Creates a download link for the file
    (also randomizes the filename base folder)
    Args:
        filename: FULL filename of the file, including the extension
    """

    ip_or_domain = os.getenv("ip_or_domain", config.get("IP_OR_DOMAIN"))

    random_string = "".join(
        random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=12)
    )
    os.makedirs(
        os.path.join(filedir, random_string), exist_ok=True
    )  # create random folder to store file inside

    os.rename(
        os.path.join(filedir, filename), os.path.join(filedir, random_string, filename)
    )  # move file into the random folder we just created

    return f"{ip_or_domain}/ytflex-cdn/{quote(random_string)}/{quote(filename)}"
