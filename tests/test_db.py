from curator import db


def test_db_insert_and_query(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    db.insert_item("vid1", "title", "desc", 10, "url", db_path=db_path)
    items = db.list_items(db_path=db_path)
    assert items
    assert items[0]["id"] == "vid1"

    db.record_rating("vid1", 7, db_path=db_path)
    ratings = db.list_ratings("vid1", db_path=db_path)
    assert ratings
    assert ratings[0]["rating"] == 7
