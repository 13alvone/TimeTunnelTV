# README.md	(tab-indented code fences instead of ```)
	Archive-Curator is a CLI + Flask tool that pulls 20–30 fresh,
	randomised Internet Archive videos every day, stores rich metadata
	in SQLite, auto-downloads up to 50 GB/day, and learns your taste
	based on 1-10 ratings.

	Usage
	-----
	1. make install        # install deps with Poetry
	2. poetry run curator fetch     # grab today’s haul
	3. poetry run curator web       # open http://<host>:5000
	4. poetry run curator rate <id> <score>

	Config (~/.curator/config.toml) lets you change:
	  daily_candidates, min/max length, seed_keywords, download_cap_gb …
