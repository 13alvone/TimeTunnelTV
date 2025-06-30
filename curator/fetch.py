from __future__ import annotations

import random
import time
from pathlib import Path
from typing import List, Dict, Any

import requests

from . import db
from .config import Config


def _sleep_for_rps(rps_limit: float) -> None:
    """Sleep enough to respect requests-per-second limit."""
    if rps_limit <= 0:
        return
    time.sleep(max(0.0, 1.0 / rps_limit))


def _best_h264_file(files: List[Dict[str, Any]]) -> tuple[str, int] | None:
    """Return (name, size) of the largest playable H.264 file."""
    best: tuple[str, int] | None = None
    for info in files:
        name = info.get("name")
        if not name:
            continue
        fmt = str(info.get("format", "")).lower()
        if "h.264" in fmt or "h264" in fmt or "mpeg4" in fmt or "quicktime" in fmt:
            size = int(info.get("size") or 0)
            if best is None or size > best[1]:
                best = (name, size)
    return best


def fetch_candidates(cfg: Config) -> List[str]:
    """Fetch and persist daily candidate items.

    Returns a list of item identifiers inserted into the database.
    """

    keywords = " OR ".join(cfg.seed_keywords)
    query = f"({keywords}) AND duration:[{cfg.min_seconds} TO {cfg.max_seconds}]"

    params = {
        "q": query,
        "fl[]": ["identifier", "title", "description", "duration"],
        "rows": cfg.daily_candidates,
        "output": "json",
        "sort[]": f"random_{random.randint(0, 99999)}",
    }

    _sleep_for_rps(cfg.rps_limit)
    res = requests.get("https://archive.org/advancedsearch.php", params=params)
    res.raise_for_status()
    docs = res.json()["response"]["docs"]

    inserted: List[str] = []

    for item in docs:
        identifier = item["identifier"]
        _sleep_for_rps(cfg.rps_limit)
        meta = requests.get(f"https://archive.org/metadata/{identifier}")
        if meta.status_code != 200:
            continue
        files = meta.json().get("files", [])
        best = _best_h264_file(files)
        if not best:
            continue
        file_name, _ = best
        url = f"https://archive.org/download/{identifier}/{file_name}"
        title = item.get("title", "")
        description = item.get("description", "") or ""
        duration = int(float(item.get("duration") or 0))
        db.insert_item(identifier, title, description, duration, url)
        inserted.append(identifier)
    return inserted


def _daily_downloaded_bytes() -> int:
    """Return sum of bytes downloaded today (UTC)."""
    with db.get_connection() as conn:
        cur = conn.execute(
            "SELECT COALESCE(SUM(size_bytes),0) FROM downloads "
            "WHERE date(downloaded_at, 'utc') = date('now','utc')"
        )
        row = cur.fetchone()
        return int(row[0] or 0)


def download_item(item_id: str, dst_dir: str | Path, cfg: Config) -> Path:
    """Download ``item_id`` respecting daily cap and record size."""
    dst_path = Path(dst_dir)
    dst_path.mkdir(parents=True, exist_ok=True)

    with db.get_connection() as conn:
        cur = conn.execute("SELECT url FROM items WHERE id = ?", (item_id,))
        row = cur.fetchone()
    if not row:
        raise ValueError(f"item {item_id} not found in database")
    url = row["url"]

    downloaded = _daily_downloaded_bytes()
    cap_bytes = cfg.download_cap_gb * 1024**3
    if downloaded >= cap_bytes:
        raise RuntimeError("daily download cap reached")

    _sleep_for_rps(cfg.rps_limit)
    r = requests.get(url, stream=True)
    r.raise_for_status()

    local = dst_path / Path(url).name
    size = 0
    with local.open("wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if not chunk:
                continue
            size += len(chunk)
            if downloaded + size > cap_bytes:
                r.close()
                raise RuntimeError("download cap reached while downloading")
            f.write(chunk)

    db.record_download(item_id, size)
    return local
