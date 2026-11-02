"""
Historical bandwidth tracking, per IP.

This is deliberately NOT a quota/rate-limit enforcer (that's slowapi's job,
via DOWNLOAD_RATE_LIMIT in config.yaml). It's a dataset for spotting an
anomaly - e.g. someone slowly trickling down a large amount of data over
many small, individually-legitimate-looking downloads, which per-request
rate limits alone wouldn't catch.

Retention mirrors suncdn's quota.py: rows older than the retention window
have their IP scrubbed (not deleted), so total historical download volume
stays visible without keeping an indefinite record of who downloaded what.
"""

import time

from src.db_handler.tables import BandwidthRecord, get_session

WEEK_SECONDS = 7 * 24 * 60 * 60
ANONYMIZED_IP = "0.0.0.0"

# Values of the client= request parameter that are stored as they are.
# Anything else is stored as "other", so a caller cannot fill the column with junk.
KNOWN_CLIENTS = {"ext"}


def record_download(ip: str, size_bytes: int, client: str = "other") -> None:
    """Log one successful download's byte count against the requesting IP and client."""
    client = client if client in KNOWN_CLIENTS else "other"
    with get_session() as session:
        session.add(
            BandwidthRecord(
                ip=ip, bytes=size_bytes, timestamp=time.time(), client=client
            )
        )
        session.commit()


def prune_old_records(older_than_seconds: float = WEEK_SECONDS) -> None:
    """
    Scrub the IP on rows past the retention window, but keep the row.

    Keeps bytes/timestamp intact so historical download volume is still
    visible later - only the ip column is touched, and only once (rows
    already scrubbed are skipped on subsequent runs).
    """
    cutoff = time.time() - older_than_seconds
    with get_session() as session:
        session.query(BandwidthRecord).filter(
            BandwidthRecord.timestamp < cutoff,
            BandwidthRecord.ip != ANONYMIZED_IP,
        ).update({BandwidthRecord.ip: ANONYMIZED_IP}, synchronize_session=False)
        session.commit()


def total_bytes_downloaded(since_seconds: float | None = None) -> int:
    """
    Convenience helper: total bytes across all recorded downloads, optionally
    restricted to the last `since_seconds`. Works whether or not the IP on a
    given row has been scrubbed, since scrubbing never touches `bytes`.
    """
    from sqlalchemy import func, select  # local import - only needed here

    with get_session() as session:
        query = select(func.coalesce(func.sum(BandwidthRecord.bytes), 0))
        if since_seconds is not None:
            query = query.where(
                BandwidthRecord.timestamp >= time.time() - since_seconds
            )
        return int(session.execute(query).scalar_one())


def downloads_by_client(
    since_seconds: float | None = None,
) -> list[tuple[str, int, int]]:
    """
    Download count and total bytes per client, e.g. [("ext", 12, 345678), ("other", 80, ...)].
    Optionally restricted to the last `since_seconds`.
    """
    from sqlalchemy import func, select  # local import - only needed here

    with get_session() as session:
        query = select(
            BandwidthRecord.client,
            func.count(),
            func.coalesce(func.sum(BandwidthRecord.bytes), 0),
        ).group_by(BandwidthRecord.client)
        if since_seconds is not None:
            query = query.where(
                BandwidthRecord.timestamp >= time.time() - since_seconds
            )
        return [(c, int(n), int(b)) for c, n, b in session.execute(query).all()]
