#!/usr/bin/env bash
set -euo pipefail

# install pipx if missing
if ! command -v pipx >/dev/null 2>&1; then
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
fi

# install poetry via pipx if missing
if ! command -v poetry >/dev/null 2>&1; then
    pipx install poetry
fi

# install project dependencies
poetry install

