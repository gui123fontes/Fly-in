PYTHON = python3
MAP ?= maps/test.txt

.PHONY: install run debug clean lint lint-strict

install:
	pip install -r requirements.txt

run:
	$(PYTHON) src/main.py $(MAP)

run-gui:
	$(MAKE) run ARGS=--gui

run-stats:
	$(MAKE) run ARGS=--stats

debug:
	$(PYTHON) -m pdb src/main.py $(MAP)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .mypy_cache

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
