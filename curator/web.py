from __future__ import annotations

from flask import Flask, render_template
from flask_cors import CORS

from . import db


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)

    @app.get("/")
    def index():
        items = db.list_items_today(limit=20)
        return render_template("index.html", items=items)

    @app.post("/rate/<item_id>/<int:score>")
    def rate(item_id: str, score: int):
        db.record_rating(item_id, score)
        return render_template("rated_fragment.html", score=score)

    return app


def main() -> None:
    create_app().run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
