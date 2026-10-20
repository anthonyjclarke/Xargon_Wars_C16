PYTHON ?= python3
NODE ?= node

.PHONY: all run run-original test compare verify probes clean docs docs-html docs-watch docs-check test-docs

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

probes: all
	$(PYTHON) scripts/probe_gameplay_rules.py

docs: all
	$(PYTHON) scripts/analyze_codebase.py
	$(NODE) scripts/build_docs.mjs

docs-html:
	$(NODE) scripts/build_docs.mjs

docs-watch:
	$(NODE) scripts/build_docs.mjs --watch

docs-check:
	$(NODE) scripts/build_docs.mjs --check

test-docs:
	$(NODE) --test test/test_docs.mjs

clean:
	rm -rf build .pio
