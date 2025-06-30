from curator import db
from curator.web import create_app


def setup_web_db(tmp_path, monkeypatch):
    db_path = tmp_path / "web.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)
    db.insert_item("vid1", "title", "desc", 10, "url", db_path=db_path)

    orig_list = db.list_items_today
    orig_record = db.record_rating
    orig_insert = db.insert_item
    monkeypatch.setattr(
        db,
        "list_items_today",
        lambda limit=20, path=db_path: orig_list(limit, db_path=path),
    )
    monkeypatch.setattr(
        db,
        "record_rating",
        lambda item_id, rating, rated_at=None, path=db_path: orig_record(
            item_id, rating, rated_at, db_path=path
        ),
    )
    monkeypatch.setattr(
        db, "insert_item", lambda *args, **kwargs: orig_insert(*args, db_path=db_path)
    )

    return db_path


def test_web_invalid_rating(monkeypatch, tmp_path):
    setup_web_db(tmp_path, monkeypatch)
    app = create_app()
    with app.test_client() as client:
        resp = client.post("/rate/vid1/0")
        assert resp.status_code == 400
