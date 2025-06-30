from __future__ import annotations

from flask import Flask, render_template_string

from . import db

HTML = """
<!doctype html>
<title>Curator</title>
<h1>Recent Items</h1>
{% for item in items %}
  <div>
    <h3>{{ item['title'] }}</h3>
    <p>{{ item['description'] or '' }}</p>
    <video width="320" controls src="{{ item['url'] }}"></video>
    <div>
      {% for i in range(1, 11) %}
        <form action="/rate/{{ item['id'] }}/{{ i }}" method="post" style="display:inline;">
          <button type="submit">{{ i }}</button>
        </form>
      {% endfor %}
    </div>
  </div>
  <hr>
{% endfor %}
"""


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        items = db.list_items(limit=20)
        return render_template_string(HTML, items=items)

    @app.post("/rate/<item_id>/<int:score>")
    def rate(item_id: str, score: int):
        db.record_rating(item_id, score)
        return "", 204

    return app


def main() -> None:
    create_app().run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
