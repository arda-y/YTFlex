"""
Utility side process to purge old files from the download directory after a certain time.
"""

import asyncio
import os
import time
import config


async def purge_old_files():
    """Purge files older than max_file_age defined in config.py from download_directory"""

    print("File purge subprocess started.")  # debug

    download_path = "./mountpoint/downloads"
    # create mountpoint if it doesn't exist
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    while True:
        max_file_age = config.get("MAX_FILE_AGE")

        await asyncio.sleep(60)  # check every minute
        for folder in os.listdir(download_path):
            folder_path = os.path.join(download_path, folder)
            if not os.path.isdir(folder_path):
                continue

            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                # get creation time of file
                last_change = os.path.getctime(file_path)
                now = time.time()
                file_age = int(now - last_change)

                if file_age > max_file_age:
                    print(f"Deleting {file}, {file_age} seconds old")
                    os.remove(file_path)

            # Remove parent directory if empty
            if not os.listdir(folder_path):
                os.rmdir(folder_path)
