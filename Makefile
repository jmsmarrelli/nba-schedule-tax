# Pipeline stages share generated inputs and must run in order.
.NOTPARALLEL:
PY ?= python3

.PHONY: all data model luck clean site

all: verify-data data model luck

data:
	$(PY) src/run_01_build.py

model:
	$(PY) src/run_02_model.py

luck:
	$(PY) src/run_03_luck.py

# Regenerate the GitHub Pages page from README.md. Needs `pip install -r requirements.txt`.
site:
	$(PY) tools/site.py

clean:
	rm -f figures/*.png output/*.csv data/processed/*

.PHONY: fetch-data verify-data
fetch-data:
	$(PY) tools/fetch_data.py

verify-data:
	$(PY) tools/fetch_data.py --check

.PHONY: report
report:
	$(PY) tools/report.py
