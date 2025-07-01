import importlib
import sys
import numpy as np
from click.testing import CliRunner

from curator import db


# Reload real modules if tests/__init__ provided stubs
if not hasattr(np, "__file__"):
    sys.modules.pop("numpy", None)
    np = importlib.import_module("numpy")

if "requests" in sys.modules and not hasattr(sys.modules["requests"], "HTTPError"):
    sys.modules.pop("requests")
if "requests" not in sys.modules:
    sys.modules["requests"] = importlib.import_module("requests")


class DummyModel:
    def __init__(self, vectors):
        self.vectors = vectors

    def encode(self, text, convert_to_numpy=True, normalize_embeddings=True):
        vec = np.array(self.vectors[text], dtype=float)
        if normalize_embeddings:
            vec = vec / np.linalg.norm(vec)
        return vec

    def get_sentence_embedding_dimension(self):
        return 2


def setup_cli_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cli.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    orig_init = db.init_db
    orig_get_conn = db.get_connection

    monkeypatch.setattr(db, "init_db", lambda path=db_path: orig_init(path))
    monkeypatch.setattr(db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path))

    return db_path, orig_get_conn


def test_cli_recommend(monkeypatch, tmp_path):
    db_path, orig_get_conn = setup_cli_db(tmp_path, monkeypatch)

    # Insert items and ratings
    db.insert_item("id1", "id1", "", 1, "url1", db_path=db_path)
    db.insert_item("id2", "id2", "", 1, "url2", db_path=db_path)
    db.insert_item("id3", "id3", "", 1, "url3", db_path=db_path)

    db.record_rating("id1", 8, db_path=db_path)
    db.record_rating("id2", 4, db_path=db_path)

    vectors = {
        "id1": [1, 0],
        "id2": [0, 1],
        "id3": [0.2, 0.8],
    }

    sentence_transformers = importlib.import_module("sentence_transformers")
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", lambda model: DummyModel(vectors))

    from curator import recommend
    from curator.cli import cli

    monkeypatch.setattr(recommend, "_model", DummyModel(vectors))
    monkeypatch.setattr(recommend.db, "get_connection", lambda db_path=db_path: orig_get_conn(db_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["recommend", "-n", "2"])

    assert result.exit_code == 0
    lines = [line.split()[0] for line in result.output.strip().splitlines()]
    assert lines == ["id1", "id3"]
