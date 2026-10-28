# pylint: disable=invalid-name
#
# API_Key is technically not PascalCase

"""This module contains the SQLAlchemy tables for the database."""

import datetime
from dataclasses import dataclass
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    SmallInteger,
    Float,
)
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from src.db_handler import _Base, _engine

__all__ = [
    "DownloadLog",
    "Api_Key",
    "BandwidthRecord",
]  # classes the objects of which are to be used in the code


def get_session():
    """Returns a new session to the database."""
    return Session(_engine)


@dataclass
class DownloadLog(_Base):
    """Table for storing download information."""

    __tablename__ = "ytflex_downloads"
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_string = Column(
        String(200), nullable=False
    )  # parsed ID of the video, can track parsing errors with this
    time_of_request = Column(
        DateTime, nullable=False, default=datetime.datetime.now
    )  # pass the time of the request no matter what
    type_of_request = Column(
        String(10), nullable=False
    )  # type of request, either "video", "audio", "playlist_video" or "playlist_audio"
    status_code = Column(SmallInteger)  # inside codes for the status of the download
    requested_resolution = Column(SmallInteger)
    downloaded_resolution = Column(SmallInteger)
    title = Column(String(100))
    duration = Column(SmallInteger)
    api_key = Column(String(40))
    file_size = Column(SmallInteger)
    time_of_response = Column(DateTime)
    playlist_url_count = Column(SmallInteger)
    custom_file_life = Column(SmallInteger)


@dataclass
class Api_Key(_Base):
    """Table for storing API keys."""

    @staticmethod
    def _default_expiration():
        """Returns datetime object of 30 days from now."""
        return datetime.datetime.now() + datetime.timedelta(days=30)

    __tablename__ = "ytflex_api_keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(40), nullable=False)
    owner = Column(String(40), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    tier = Column(SmallInteger, default=1)
    is_active = Column(Boolean, default=True)
    additional_file_life_requested = Column(SmallInteger, default=0)  # in hours
    credits_used = Column(
        Integer, default=0
    )  # hours * video size, no penalty for < 1 hour
    last_used = Column(DateTime)
    last_ip = Column(String(20))
    usage_count = Column(Integer, default=0, autoincrement=True)
    expires_at = Column(DateTime, default=_default_expiration)


@dataclass
class BandwidthRecord(_Base):
    """
    One row per successful download: how many bytes, from which IP, when.

    Mirrors suncdn's UploadRecord/quota.py pattern - this is a historical
    bandwidth dataset (so a slow trickle of many small downloads shows up
    as an anomaly over time), not a per-request quota enforcer. See
    bandwidth.py's prune_old_records() for the same "scrub IP after 7 days,
    keep the row" retention behavior used there.
    """

    __tablename__ = "ytflex_bandwidth_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(45), nullable=False, index=True)
    bytes = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False, index=True)
    # Which kind of caller made the request: "ext" for the browser extension
    # (client=ext), "other" for everything else. See bandwidth.KNOWN_CLIENTS.
    client = Column(String(16), nullable=False, default="other", server_default="other")


# Create all tables in the database
# This is equivalent to "Create Table" statements in raw SQL
_Base.metadata.create_all(_engine)


def _add_missing_columns():
    """
    create_all never alters a table that already exists, so a column added to a
    model later has to be added by hand. Safe to run on every start.
    Rows written before the column existed get the default value ("other").
    """
    with _engine.begin() as conn:
        columns = {c["name"] for c in inspect(conn).get_columns("ytflex_bandwidth_records")}
        if "client" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE ytflex_bandwidth_records "
                    "ADD COLUMN client VARCHAR(16) NOT NULL DEFAULT 'other'"
                )
            )


_add_missing_columns()
