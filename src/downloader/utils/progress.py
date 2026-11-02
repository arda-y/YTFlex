"""
In-memory download progress, polled by the page through GET /progress/{id}.

Entries are keyed by an id the client makes up, are never written to disk, and
expire a few minutes after their last update.
"""

import re
import threading
import time

_TTL_SECONDS = 600
_ID_RE = re.compile(r"^[A-Za-z0-9]{8,32}$")

_progress: dict[str, dict] = {}
_lock = threading.Lock()


def valid_id(progress_id: str | None) -> bool:
    """True if the id is safe to use as a key."""
    return bool(progress_id) and bool(_ID_RE.match(progress_id))


def _prune(now: float) -> None:
    for key in [k for k, v in _progress.items() if now - v["t"] > _TTL_SECONDS]:
        del _progress[key]


def update(progress_id: str, **fields) -> None:
    """Merges fields into the entry for this id."""
    now = time.time()
    with _lock:
        _prune(now)
        entry = _progress.setdefault(progress_id, {"stage": "starting", "percent": 0})
        if (
            fields.get("stage", entry["stage"]) != entry["stage"]
            or "stage_since" not in entry
        ):
            entry["stage_since"] = now
        entry.update(fields)
        entry["t"] = now


def get(progress_id: str) -> dict | None:
    """Returns the public view of an entry (plus seconds spent in the current stage), or None if unknown."""
    with _lock:
        entry = _progress.get(progress_id)
        if entry is None:
            return None
        view = {k: v for k, v in entry.items() if k not in ("t", "stage_since")}
        view["elapsed"] = int(time.time() - entry.get("stage_since", entry["t"]))
        return view


# A video request downloads two streams (video, then the much smaller audio) and merges them.
# yt-dlp names such intermediate files "<title>.f<format id>.<ext>"; a single-file download has no such part.
_PART_RE = re.compile(r"\.f[\w-]+\.[A-Za-z0-9]+$")
_FIRST_STREAM_SHARE = 0.85

# What the slow post-processing steps are called on the page. Conversion has no real percentage
# (yt-dlp does not report ffmpeg progress), so the page shows the stage and the time spent in it.
_PP_STAGES = {
    "Merger": "merging",
    "VideoConvertor": "converting",
    "ExtractAudio": "converting",
}


def make_hooks(progress_id: str):
    """Returns (download_hook, postprocessor_hook) for yt-dlp that feed this id.

    percent is for the whole job, not per stream: when two streams are being merged the
    first one fills 0-85% and the second 85-100%, so the bar never jumps back to 0."""
    files: list[str] = []

    def overall(filename: str, fraction: float) -> int:
        if filename not in files:
            files.append(filename)
        merging = bool(_PART_RE.search(files[0]))
        if not merging:
            return int(fraction * 100)
        if files.index(filename) == 0:
            return int(fraction * _FIRST_STREAM_SHARE * 100)
        return int((_FIRST_STREAM_SHARE + fraction * (1 - _FIRST_STREAM_SHARE)) * 100)

    def download_hook(d):
        name = d.get("filename") or ""
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            fraction = min(done / total, 1.0) if total else 0.0
            update(progress_id, stage="downloading", percent=overall(name, fraction))
        elif d["status"] == "finished":
            # more streams may follow; the post-processing stages start with the first postprocessor
            update(progress_id, percent=overall(name, 1.0))

    def postprocessor_hook(d):
        if d["status"] == "started":
            update(
                progress_id,
                stage=_PP_STAGES.get(d.get("postprocessor"), "finishing"),
                percent=100,
            )

    return download_hook, postprocessor_hook
