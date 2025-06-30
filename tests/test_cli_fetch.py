from click.testing import CliRunner
import pytest

from curator import db

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


def setup_fetch_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cli.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    orig_init = db.init_db
    orig_insert = db.insert_item
    orig_record_dl = db.record_download
    orig_get_conn = db.get_connection

    monkeypatch.setattr(db, "init_db", lambda path=db_path: orig_init(path))
    monkeypatch.setattr(db, "insert_item", lambda *a, **kw: orig_insert(*a, db_path=db_path))
    monkeypatch.setattr(db, "record_download", lambda *a, **kw: orig_record_dl(*a, db_path=db_path))
    monkeypatch.setattr(db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path))

    return db_path, orig_get_conn


def test_cli_fetch(monkeypatch, tmp_path):
    db_path, orig_get_conn = setup_fetch_db(tmp_path, monkeypatch)
    from curator import fetch
    from curator import cli
    from curator.config import Config

    # ensure fetch module uses patched connection
    monkeypatch.setattr(fetch.db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path))
    monkeypatch.setattr(fetch, "_sleep_for_rps", lambda x: None)

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
            return FakeResponse({"files": [{"name": "video.mp4", "format": "h.264", "size": "10"}]})
        elif "download" in url:
            return FakeResponse(content=b"abc")
        raise RuntimeError("unexpected url" + url)

    monkeypatch.setattr(fetch.requests, "get", fake_get)

    monkeypatch.setattr(cli, "load_config", lambda: Config(daily_candidates=1, seed_keywords=["x"], rps_limit=0))

    runner = CliRunner()
    download_dir = tmp_path / "downloads"
    result = runner.invoke(cli.cli, ["fetch", "-d", str(download_dir)])
    assert result.exit_code == 0
    assert "Fetched 1 candidates" in result.output
    assert "Downloaded id1" in result.output

    items = db.list_items(db_path=db_path)
    assert items and items[0]["id"] == "id1"
    assert (download_dir / "video.mp4").exists()

