import textwrap
from pathlib import Path
from curator.config import load_config, DEFAULT_CONFIG


def test_load_config_without_user_file(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    cfg = load_config()
    assert cfg == DEFAULT_CONFIG


def test_load_config_with_user_file(monkeypatch, tmp_path):
    cfg_dir = tmp_path / ".curator"
    cfg_dir.mkdir()
    (cfg_dir / "config.toml").write_text(
        textwrap.dedent(
            """
            daily_candidates = 5
            seed_keywords = ["cats"]
            """
        )
    )
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    cfg = load_config()
    assert cfg.daily_candidates == 5
    assert cfg.seed_keywords == ["cats"]
    assert cfg.max_seconds == DEFAULT_CONFIG.max_seconds
