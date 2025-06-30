from curator import db
from curator.config import Config


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
    monkeypatch.setattr(db, "insert_item", lambda *args, **kwargs: orig_insert(*args, db_path=db_path))

    from curator import fetch

    def fake_get(url, params=None, stream=False):
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
        else:
            raise RuntimeError("unexpected url" + url)

    monkeypatch.setattr(fetch, "_sleep_for_rps", lambda x: None)
    monkeypatch.setattr(fetch.requests, "get", fake_get)

    cfg = Config(daily_candidates=1, seed_keywords=["x"], rps_limit=0)
    ids = fetch.fetch_candidates(cfg)
    assert ids == ["id1"]
    items = db.list_items(db_path=db_path)
    assert items[0]["id"] == "id1"
