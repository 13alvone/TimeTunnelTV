from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import List


@dataclass
class Config:
    """Configuration values for curator."""

    daily_candidates: int = 30
    min_seconds: int = 5
    max_seconds: int = 18_000  # 5 hours
    seed_keywords: List[str] = field(default_factory=list)
    download_cap_gb: int = 50
    rps_limit: float = 1.0
    timeout: float = 10.0


DEFAULT_CONFIG = Config(
    seed_keywords=["funny", "crazy", "interesting"],
)


def load_config() -> Config:
    """Return configuration merged with ``~/.curator/config.toml`` if present."""

    path = Path.home() / ".curator" / "config.toml"
    if path.is_file():
        with path.open("rb") as f:
            data = tomllib.load(f)
    else:
        data = {}

    cfg_dict = dataclasses.asdict(DEFAULT_CONFIG)
    cfg_dict.update({k: v for k, v in data.items() if k in cfg_dict})

    return Config(**cfg_dict)
