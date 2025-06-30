from __future__ import annotations

import click

import logging

from . import db, fetch as fetch_module, recommend as recommend_module
from .config import load_config


logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """Curator command line interface."""
    db.init_db()
    logger.info("[i] database initialised")


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
    logger.info("[i] fetched %d candidates", len(ids))
    click.echo(f"Fetched {len(ids)} candidates")
    for item_id in ids:
        try:
            path = fetch_module.download_item(item_id, directory, cfg)
            logger.info("[i] downloaded %s", item_id)
            click.echo(f"Downloaded {item_id} -> {path}")
        except Exception as e:  # noqa: BLE001
            logger.error("[x] %s", e)
            click.echo(f"Failed {item_id}: {e}", err=True)


@cli.command(name="list")
@click.option("-n", default=10, help="number of items")
def list_items(n: int) -> None:
    """List recent items."""
    rows = db.list_items(limit=n)
    logger.info("[i] listing %d items", n)
    for row in rows:
        click.echo(f"{row['id']} - {row['title']}")


@cli.command()
@click.argument("item_id")
@click.argument("score", type=int)
def rate(item_id: str, score: int) -> None:
    """Record a rating for an item."""
    try:
        db.record_rating(item_id, score)
    except ValueError as e:
        logger.error("[!] %s", e)
        click.echo(str(e), err=True)
        raise SystemExit(1)
    logger.info("[i] rated %s %d", item_id, score)
    click.echo(f"Rated {item_id} {score}")


@cli.command()
@click.option("-n", default=10, help="number of recommendations")
def recommend(n: int) -> None:
    """Print recommended items."""
    rows = recommend_module.recommend(n)
    logger.info("[i] recommended %d items", n)
    for row in rows:
        click.echo(f"{row['id']} - {row['title']}")


@cli.command()
def web() -> None:
    """Run the Flask web UI."""
    from . import web as web_module

    app = web_module.create_app()
    logger.info("[i] starting web UI on :5000")
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    cli()
