.DEFAULT_GOAL := help

install: ## Install project deps via poetry
	poetry install

run-cli: ## Example: run daily fetch
	poetry run curator fetch

run-server: ## Serve Flask UI
	poetry run curator web

lint: ## Format with black
	poetry run black curator

test: ## Run unit tests
	poetry run pytest -q

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
