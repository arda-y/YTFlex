"""
Utility function to check if a URL is valid.
"""

from urllib.parse import urlparse, parse_qs, unquote


def parse_video_id(link: str) -> str | bool:
    """
    Checks if a URL is valid or not, and parses video IDs as well.

    Args:
        link: The URL to check.
    Returns:
        True if the URL is valid, False otherwise.
    """

    quick_parsable = [
        "/watch/",
        "/v/",
        "/embed/",
        "/shorts/",
        "/live/",
        "/e/",
    ]

    parsable = urlparse(link)

    if parsable.path == "/watch":
        video_id = parse_qs(parsable.query).get("v", [None])[0]
    elif parsable.path == "/oembed":
        link = parse_qs(parsable.query).get("url", [None])
        video_id = parse_video_id(unquote(link[0]))
    elif parsable.path.startswith("/attribution_link"):
        partial_link = unquote(parse_qs(parsable.query).get("u", [None])[0])
        video_id = parse_video_id(f"https://youtube.com{partial_link}")
    elif parsable.path.startswith("/"):
        video_id = parsable.path.split("/")[1][:11]

    for prefix in quick_parsable:
        if parsable.path.startswith(prefix):
            video_id = parsable.path.split(prefix)[1][:11]

    if len(video_id) == 11:
        return video_id

    return False  # catch all failure case


if __name__ == "__main__":
    with open("test_links.txt", "r", encoding="utf-8") as f:
        for line in f:
            assert len(parse_video_id(line.strip())) == 11

        print("passing")
