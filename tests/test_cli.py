from click.testing import CliRunner
from curator import db


def setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cli.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)
    db.insert_item("vid1", "title", "desc", 10, "url", db_path=db_path)

    orig_init = db.init_db
    orig_list = db.list_items
    orig_record = db.record_rating
    orig_insert = db.insert_item
    monkeypatch.setattr(db, "init_db", lambda path=db_path: orig_init(path))
    monkeypatch.setattr(
        db, "list_items", lambda limit=100, path=db_path: orig_list(limit, db_path=path)
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


def test_cli_rate_and_list(monkeypatch, tmp_path):
    setup_db(tmp_path, monkeypatch)
    from curator.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["rate", "vid1", "8"])
    assert result.exit_code == 0
    assert "Rated vid1 8" in result.output

    result = runner.invoke(cli, ["list", "-n", "1"])
    assert result.exit_code == 0
    assert "vid1 - title" in result.output


def test_cli_invalid_rating(monkeypatch, tmp_path):
    setup_db(tmp_path, monkeypatch)
    from curator.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["rate", "vid1", "11"])
    assert result.exit_code != 0
    assert "between 1 and 10" in result.output
