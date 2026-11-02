"""
Database handler package for the ytflex project.
Contains the database engine and the base object for all tables.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
import config

__all__ = ["_engine", "_Base"]  # private namespace since it won't leave the package

_db_string = config.get(
    "database_url",
    f"sqlite:///{Path(__file__).resolve().parent.parent.parent.as_posix()}"
    + "/mountpoint/database/ytflex_database.db",
)  # unstylish but os agnostic

# sqlite won't create a missing parent directory on its own - nothing else
# in this project creates mountpoint/database/, so do it here before the
# engine tries to open a connection. Guarded to sqlite:/// URLs only, since
# database_url can be overridden to something else entirely via config.
if _db_string.startswith("sqlite:///"):
    Path(_db_string.removeprefix("sqlite:///")).parent.mkdir(
        parents=True, exist_ok=True
    )

# Create the database engine
_engine = create_engine(_db_string)

# Base object for all tables
_Base = declarative_base()
# if you're creating a new table, import _Base from here
# and inherit from it in your table class
