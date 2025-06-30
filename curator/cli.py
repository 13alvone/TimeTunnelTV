from __future__ import annotations

import click

from . import db, fetch as fetch_module, recommend as recommend_module
from .config import load_config


@click.group()
def cli() -> None:
    """Curator command line interface."""
    db.init_db()


@cli.command()
@click.option(
    "-d",
    "directory",
    default="downloads",
    type=click.Path(file_okay=False, dir_okay=True),
)
def fetch(directory: str) -> None:
    """Fetch daily candidates and download them."""
    cfg = load_config()
    ids = fetch_module.fetch_candidates(cfg)
    click.echo(f"Fetched {len(ids)} candidates")
    for item_id in ids:
        try:
            path = fetch_module.download_item(item_id, directory, cfg)
            click.echo(f"Downloaded {item_id} -> {path}")
        except Exception as e:  # noqa: BLE001
            click.echo(f"Failed {item_id}: {e}", err=True)


@cli.command(name="list")
@click.option("-n", default=10, help="number of items")
def list_items(n: int) -> None:
    """List recent items."""
    rows = db.list_items(limit=n)
    for row in rows:
        click.echo(f"{row['id']} - {row['title']}")


@cli.command()
@click.argument("item_id")
@click.argument("score", type=int)
def rate(item_id: str, score: int) -> None:
    """Record a rating for an item."""
    db.record_rating(item_id, score)
    click.echo(f"Rated {item_id} {score}")


@cli.command()
@click.option("-n", default=10, help="number of recommendations")
def recommend(n: int) -> None:
    """Print recommended items."""
    rows = recommend_module.recommend(n)
    for row in rows:
        click.echo(f"{row['id']} - {row['title']}")


@cli.command()
def web() -> None:
    """Run the Flask web UI."""
    from . import web as web_module

    app = web_module.create_app()
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    cli()
