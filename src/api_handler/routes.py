"""
All API routes for the YTFlex project.
"""
from fastapi.responses import FileResponse

from src.api_handler.app import app
from src.downloader.runner import download_files

__all__ = ["root", "audio_download", "video_download"]



import os

@app.get("/")
async def home():
    """Home route for the API."""
    # Ensure the path points to where your index.html is stored
    # Path.join helps avoid issues between Windows/Linux environments
    # index.html is at root dir, and this file is in src/api_handler, so we go up two levels
    file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'index.html')

    return FileResponse(file_path)

@app.get("/root")
async def root():
    """To check if the server is running without much hassle."""

    return {"message": "Hello World"}


@app.get("/download/audio")
async def audio_download(link: str):
    """API route for downloading audio files."""

    # bundle the download info
    raw_dl_info = download_files(passed_url=link, is_video_request=False)

    return raw_dl_info


@app.get("/download/video")
async def video_download(link: str, res: str | int, mp4: bool = False):
    """API route for downloading video files."""

    raw_dl_info = download_files(
        passed_url=link, is_video_request=True, preferred_res=res, convert_to_mp4=mp4
    )

    return raw_dl_info
