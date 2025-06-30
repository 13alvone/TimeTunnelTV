from curator import db, USER_AGENT
from curator.config import Config
import pytest
import datetime


class FakeResponse:
    def __init__(self, json_data=None, status_code=200, content=b"data"):
        self._json = json_data
        self.status_code = status_code
        self._content = content

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def iter_content(self, chunk_size=8192):
        yield self._content


def test_fetch_candidates(monkeypatch, tmp_path):
    db_path = tmp_path / "fetch.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    orig_insert = db.insert_item
    monkeypatch.setattr(
        db, "insert_item", lambda *args, **kwargs: orig_insert(*args, db_path=db_path)
    )

    from curator import fetch

    def fake_get(url, params=None, stream=False, timeout=None, headers=None):
        if "advancedsearch" in url:
            data = {
                "response": {
                    "docs": [
                        {
                            "identifier": "id1",
                            "title": "Title",
                            "description": "Desc",
                            "duration": 10,
                        }
                    ]
                }
            }
            return FakeResponse(data)
        elif "metadata" in url:
            return FakeResponse(
                {"files": [{"name": "video.mp4", "format": "h.264", "size": "10"}]}
            )
        else:
            raise RuntimeError("unexpected url" + url)

    monkeypatch.setattr(fetch, "_sleep_for_rps", lambda x: None)
    monkeypatch.setattr(fetch.requests, "get", fake_get)

    cfg = Config(daily_candidates=1, seed_keywords=["x"], rps_limit=0)
    ids = fetch.fetch_candidates(cfg)
    assert ids == ["id1"]
    items = db.list_items(db_path=db_path)
    assert items[0]["id"] == "id1"


def test_user_agent_header(monkeypatch):
    from curator import fetch

    calls = []

    def fake_get(url, params=None, stream=False, timeout=None, headers=None):
        calls.append(headers)
        return FakeResponse({"response": {"docs": []}})

    monkeypatch.setattr(fetch, "_sleep_for_rps", lambda x: None)
    monkeypatch.setattr(fetch.requests, "get", fake_get)

    cfg = Config(daily_candidates=1, seed_keywords=["x"], rps_limit=0)
    fetch.fetch_candidates(cfg)

    assert calls and calls[0].get("User-Agent") == USER_AGENT


def test_timeout_passed(monkeypatch, tmp_path):
    db_path = tmp_path / "timeout.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    orig_insert = db.insert_item
    monkeypatch.setattr(
        db, "insert_item", lambda *args, **kwargs: orig_insert(*args, db_path=db_path)
    )
    orig_record_dl = db.record_download
    monkeypatch.setattr(
        db,
        "record_download",
        lambda *args, **kwargs: orig_record_dl(*args, db_path=db_path),
    )
    orig_get_conn = db.get_connection
    monkeypatch.setattr(
        db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path)
    )

    from curator import fetch

    monkeypatch.setattr(
        fetch.db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path)
    )

    calls = []

    def fake_get(url, params=None, stream=False, timeout=None, headers=None):
        calls.append(timeout)
        if "advancedsearch" in url:
            data = {
                "response": {
                    "docs": [
                        {
                            "identifier": "id1",
                            "title": "Title",
                            "description": "Desc",
                            "duration": 10,
                        }
                    ]
                }
            }
            return FakeResponse(data)
        elif "metadata" in url:
            return FakeResponse(
                {"files": [{"name": "video.mp4", "format": "h.264", "size": "10"}]}
            )
        elif "download" in url:
            return FakeResponse(content=b"abc")
        else:
            raise RuntimeError("unexpected url" + url)

    monkeypatch.setattr(fetch, "_sleep_for_rps", lambda x: None)
    monkeypatch.setattr(fetch.requests, "get", fake_get)

    cfg = Config(daily_candidates=1, seed_keywords=["x"], rps_limit=0, timeout=9)
    ids = fetch.fetch_candidates(cfg)
    fetch.download_item(ids[0], tmp_path, cfg)
    assert all(t == cfg.timeout for t in calls)


def test_partial_download_cleanup(monkeypatch, tmp_path):
    db_path = tmp_path / "cap.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    orig_record_dl = db.record_download
    monkeypatch.setattr(
        db,
        "record_download",
        lambda *args, **kwargs: orig_record_dl(*args, db_path=db_path),
    )
    orig_get_conn = db.get_connection
    monkeypatch.setattr(
        db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path)
    )

    from curator import fetch

    monkeypatch.setattr(
        fetch.db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path)
    )
    monkeypatch.setattr(fetch, "_sleep_for_rps", lambda x: None)

    db.insert_item(
        "vid2",
        "title",
        "desc",
        10,
        "http://example.com/file.bin",
        db_path=db_path,
    )

    class StreamResp:
        def __init__(self, chunks):
            self.chunks = chunks
            self.status_code = 200

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            for c in self.chunks:
                yield c

        def close(self):
            pass

    def fake_get(url, stream=False, timeout=None, headers=None):
        return StreamResp([b"a" * 150, b"b" * 100])

    monkeypatch.setattr(fetch.requests, "get", fake_get)

    cfg = Config(download_cap_gb=0.0000002, seed_keywords=[], rps_limit=0)
    with pytest.raises(RuntimeError):
        fetch.download_item("vid2", tmp_path, cfg)

    assert not (tmp_path / "file.bin").exists()


def test_best_h264_file():
    """Select the largest playable H.264 file."""
    from curator import fetch

    files = [
        {"name": "a.mov", "format": "QuickTime", "size": "5"},
        {"name": "b.mp4", "format": "H.264", "size": "10"},
        {"name": "c.mp4", "format": "mpeg4", "size": "30"},
        {"name": "d.mp4", "format": "VP9", "size": "40"},
        {"name": "e.mp4", "format": "h264", "size": "50"},
    ]

    best = fetch._best_h264_file(files)

    assert best == ("e.mp4", 50)


def test_best_h264_file_none():
    """Return ``None`` when no suitable file exists."""
    from curator import fetch

    files = [
        {"name": "a.mkv", "format": "VP9", "size": "5"},
        {"name": "b.webm", "format": "vp8", "size": "10"},
    ]

    best = fetch._best_h264_file(files)

    assert best is None


def test_daily_downloaded_bytes(monkeypatch, tmp_path):
    """Only today's downloads are summed."""
    db_path = tmp_path / "daily.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    orig_record_dl = db.record_download
    monkeypatch.setattr(
        db,
        "record_download",
        lambda *a, **kw: orig_record_dl(*a, db_path=db_path, **kw),
    )
    orig_get_conn = db.get_connection
    monkeypatch.setattr(db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path))

    from curator import fetch

    monkeypatch.setattr(fetch.db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path))

    today = datetime.datetime.utcnow().date()
    yesterday = today - datetime.timedelta(days=1)

    db.record_download("t1", 100, downloaded_at=f"{today} 00:00:00")
    db.record_download("y1", 200, downloaded_at=f"{yesterday} 12:00:00")
    db.record_download("t2", 300, downloaded_at=f"{today} 23:59:59")

    assert fetch._daily_downloaded_bytes() == 400
