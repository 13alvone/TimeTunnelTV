# TimeTunnel TV

TimeTunnel TV turns any Linux box (CPU-only or CUDA) into a personalised worm-
hole through the Internet Archive. A daily job fetches 20-30 videos that match
your seed keywords, stores full metadata in SQLite, auto-downloads within a
50 GB/day cap, and refines future picks from your 1-10 ratings. You interact
either from a rich CLI or a zero-config Flask site on your LAN.

## Features
* Daily candidate pull via IA **Advanced Search + Scrape** APIs  
* Configurable duration window (5 s - 5 h default) & keyword bias  
* Rich metadata persistence (`items`, `ratings`, `downloads` tables)  
* Auto-download best H.264 file; cap enforced per UTC-day  
* Sentence-Transformers embeddings (CUDA if available) for taste learning  
* Robust `[i]/[!]/[DEBUG]/[x]` logging and WAL-backed SQLite  
* Self-contained: only Python 3.12+, Requests, Flask, Sentence-Transformers  
* Makefile + install.sh for one-shot bootstrap; Dockerfile coming v1.0

## Quick-start
        ./install.sh                         # installs pipx → Poetry → deps
        make run-cli                          # run curator fetch
        make run-server                       # start Flask UI
        poetry run curator rate <IA_ID> 7     # CLI rating

## Directory layout
project/
├─ Makefile
├─ install.sh
├─ pyproject.toml
├─ README.md
└─ curator/
    ├─ config.py	# load + merge ~/.curator/config.toml
    ├─ db.py		# SQLite schema & helpers
    ├─ fetch.py		# API queries + downloader
    ├─ recommend.py	# cosine-sim taste engine
    ├─ cli.py		# argparse front-end
    └─ web.py		# Flask UI

## Makefile commands
        make install        # install deps via poetry
        make run-cli        # run curator fetch
        make run-server     # launch Flask UI
        make lint           # format with black


## Configuration (`~/.curator/config.toml`)
	tabdaily_candidates	= 30
	tabmin_seconds		= 5
	tabmax_seconds		= 18000		# 5 h
	tabseed_keywords	= ["funny","crazy","interesting", … ]
	tabdownload_cap_gb	= 50
	tabrps_limit		= 1.0		# polite API rate

## CLI cheatsheet
	tabcurator fetch -d ~/archive_videos		# daily sync
	tabcurator list -n 20				# recent items
	tabcurator rate <id> 9				# score 1-10
	tabcurator recommend -n 10			# show similarity ranking

## Web UI endpoints
	/		today’s picks + 10 buttons (1-10) per video  
	/rate/<id>/<score>	HTMX POST, no reload  

## Internals
* **Fetcher** builds a Lucene query, random-seeds sorting, enriches each doc
  with `/metadata`, picks the best playable file, and streams it to disk while
  updating the `downloads` table.
* **Recommender** embeds title + description to 384-dim vectors and stores
  nothing—vectors live in RAM; preference vector is the rating-weighted mean.
* **Scheduler** (via cron, systemd-timer, or Kubernetes CronJob) just calls
  `curator fetch`; the rest is on-demand.

## Scheduling
Run `poetry run curator fetch` once per day so new videos are picked up. Use
`-d` to point at a directory with plenty of free space (e.g. `/srv/timetunnel`).
The host must have Internet access for downloads to work.

### Cron example
        30 2 * * * cd /opt/TimeTunnelTV && poetry run curator fetch -d /srv/timetunnel

### Systemd service and timer
Create ``timetunnel.service``:

        [Unit]
        Description=TimeTunnel daily fetch
        After=network-online.target

        [Service]
        Type=oneshot
        WorkingDirectory=/opt/TimeTunnelTV
        ExecStart=/usr/local/bin/poetry run curator fetch -d /srv/timetunnel

And ``timetunnel.timer``:

        [Unit]
        Description=Run TimeTunnel each day

        [Timer]
        OnCalendar=daily
        Persistent=true

        [Install]
        WantedBy=timers.target

Enable with ``systemctl enable --now timetunnel.timer``.

## Extending
* Swap `sentence-transformers` for a local LLM embedding file—just edit
  `recommend.py`→`MODEL`.
* Add more tables (e.g. `users`) or rating-weighted decay to taste vector.
* Dockerise: base on `python:3.12-slim`, expose `5000`, mount `~/.curator`.

## Logging
	tab2025-06-29 18:51:03 [INFO] curator.fetch: [i] AdvancedSearch …
	tab2025-06-29 18:51:14 [WARNING] curator.fetch: [!] Cap hit …

## Troubleshooting
* **Makefile “missing separator”**: ensure recipe lines start with TAB.  
* **Poetry “group” error**: upgrade Poetry ≥ 1.2 or replace with
  `[tool.poetry.dev-dependencies]`.

## License
MIT — do what you want, just don’t melt the Archive’s servers.

## Roadmap
* CUDA-accelerated embeddings on the 3080  
* Per-user profiles & auth tokens  
* Docker Compose + Grafana metrics dashboard  
* Optional Plex-style NFO export

TimeTunnel TV: because YouTube’s algorithm forgot the good stuff.

