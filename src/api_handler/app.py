"""
This file contains the FastAPI app.
It also runs the sub-processes in the background.
"""

import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from src.api_handler.side_processes.base import purge_old_files
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import config

app = FastAPI(docs_url="/docs", redoc_url=None)
origins = config.get("ALLOWED_DOMAINS")
download_rate_limit = config.get("DOWNLOAD_RATE_LIMIT", "10/minute")


def get_docker_gateway_ip() -> str | None:
    """
    Reads /proc/net/route to find the default gateway IP as seen from inside
    this container. This is the Docker bridge gateway, which nginx (running on
    the host) appears as when it reaches this container through Docker's
    published-port path.

    Docker can reassign this IP whenever the compose network is recreated
    (e.g. after `docker compose down`), so we resolve it at each startup
    instead of relying only on the hardcoded guesses in config.yaml, which go
    stale.
    """
    try:
        with open("/proc/net/route", encoding="ascii") as f:
            for line in f.readlines()[1:]:
                fields = line.strip().split()
                if len(fields) < 3:
                    continue
                if fields[1] == "00000000":  # destination 0.0.0.0 = default route
                    gateway_int = int(fields[2], 16)
                    # /proc/net/route stores the gateway in little-endian hex
                    gateway_bytes = gateway_int.to_bytes(4, byteorder="little")
                    return ".".join(str(b) for b in gateway_bytes)
    except (OSError, ValueError):
        pass
    return None


def _load_trusted_proxies() -> set[str]:
    trusted_proxies = config.get("TRUSTED_PROXIES", ["127.0.0.1"])
    if not isinstance(trusted_proxies, list):
        raise ValueError("TRUSTED_PROXIES must be a list in config.yaml.")

    parsed_proxies = {
        str(proxy).strip() for proxy in trusted_proxies if str(proxy).strip()
    }

    gateway_ip = get_docker_gateway_ip()
    if gateway_ip:
        parsed_proxies.add(gateway_ip)

    if not parsed_proxies:
        raise ValueError("TRUSTED_PROXIES cannot be empty in config.yaml.")

    return parsed_proxies


TRUSTED_PROXIES = _load_trusted_proxies()


def get_client_ip(request: Request) -> str:
    """Returns the real client IP only when the immediate peer is trusted."""

    peer_ip = request.client.host if request.client else ""

    if peer_ip in TRUSTED_PROXIES:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            first_ip = forwarded_for.split(",")[0].strip()
            if first_ip:
                return first_ip

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            parsed_real_ip = real_ip.strip()
            if parsed_real_ip:
                return parsed_real_ip

    return peer_ip or "unknown-client"


def limiter_key(request: Request) -> str:
    """Generates SlowAPI key from the trusted client IP helper."""

    return get_client_ip(request)


def rate_limit_exceeded_handler(
    _request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Returns a consistent error payload when a rate limit is exceeded."""

    return JSONResponse(status_code=429, content={"detail": str(exc)})


if not isinstance(download_rate_limit, str) or not download_rate_limit.strip():
    raise ValueError("DOWNLOAD_RATE_LIMIT must be a non-empty string in config.yaml.")

limiter = Limiter(key_func=limiter_key)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=sorted(TRUSTED_PROXIES))

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
