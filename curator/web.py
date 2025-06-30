from __future__ import annotations

from flask import Flask, render_template
from flask_cors import CORS
import logging

from . import db


logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)
    logger.info("[i] web app created")

    @app.get("/")
    def index():
        items = db.list_items_today(limit=20)
        logger.debug("serving index with %d items", len(items))
        return render_template("index.html", items=items)

    @app.post("/rate/<item_id>/<int:score>")
    def rate(item_id: str, score: int):
        try:
            db.record_rating(item_id, score)
        except ValueError as e:
            logger.warning("[!] %s", e)
            return str(e), 400
        logger.info("[i] rated %s %d via web", item_id, score)
        return render_template("rated_fragment.html", score=score)

    return app


def main() -> None:
    logger.info("[i] running web UI on :5000")
    create_app().run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
