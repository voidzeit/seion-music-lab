# SEION Music Lab — developer convenience targets.
# On Windows, run these via `make` (Git Bash / MSYS) or just copy the commands.

.PHONY: install install-dev test lint format generate clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check app tests

format:
	ruff format app tests

# Generate the default warm/hypnotic loop (Computer Data + NTO).
generate:
	seion-music generate --style "Computer Data,NTO" --key "A minor" --bpm 124 --bars 16 --emotion "warm,melancholic,hypnotic"

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('data/projects').glob('idea_*')]"
