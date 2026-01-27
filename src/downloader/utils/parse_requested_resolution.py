"""
Utility to find the appropriate resolution to download.
"""

import config


def parse_requested_resolution(requested_res: int | str):
    """
    Sanitizes the requested resolution, ensuring it is within acceptable bounds.

    Also attempts to convert the passed resolution to an integer if it is a string.

    Args:
        preferred_res: The preferred resolution to download. Accepts both int and str types, and "max"/"best" keywords.
    """

    max_res: int = config.get("MAX_RES")

    if isinstance(requested_res, str):
        if requested_res in ["max", "maximum", "best", "highest"]:
            return max_res
        elif requested_res.isdigit():
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
    elif requested_res < 0:
        return None
    else:
        return requested_res
