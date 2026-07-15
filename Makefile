.PHONY: install dev test lint clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build:
	pip install build && python -m build
