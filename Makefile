.PHONY: install dev test lint format run clean

install:
	pip install -e .
	playwright install chromium

dev:
	pip install -e ".[dev]"
	playwright install chromium

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

run:
	content-pilot run

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
