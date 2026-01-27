"""
A post processor that collects the filename of the downloaded video.
"""

from yt_dlp.postprocessor.common import PostProcessor


class FilenameCollectorPP(PostProcessor):
    """
    A post processor that collects the filename of the downloaded video.
    Access the last downloaded filename by using:

    obj.filenames[-1]

    You might need to use os.path.basename() to get the actual
    filename if you've set a custom directory.
    """

    def __init__(self):
        super().__init__(None)
        self.filenames = []

    def run(self, information):
        """Collects the filename of the downloaded video."""
        self.filenames.append(information["filepath"])
        return [], information
