PYTHON ?= python3
NODE ?= node

.PHONY: all run run-original test compare verify clean docs docs-html docs-watch docs-check test-docs

all:
	$(PYTHON) scripts/restore_c16.py

run: all
	$(PYTHON) scripts/run_vice.py

run-original:
	$(PYTHON) scripts/run_vice.py --original

test:
	$(PYTHON) -m unittest discover -s test -p 'test_*.py' -v

compare: all
	$(PYTHON) scripts/compare_reference.py

verify: compare
	$(PYTHON) scripts/verify_vice.py

clean:
	rm -rf build .pio
