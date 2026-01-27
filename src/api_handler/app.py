"""
This file contains the FastAPI app.
It also runs the sub-processes in the background.
"""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api_handler.side_processes.base import purge_old_files
import config

app = FastAPI(docs_url="/docs", redoc_url=None)
origins = config.get("ALLOWED_DOMAINS")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")  # run this function when the server starts
async def startup_event():
    """Creates sub-processes to run in the background when the server starts."""
    asyncio.create_task(purge_old_files())
