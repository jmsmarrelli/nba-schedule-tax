PY := python3

.PHONY: all data model luck clean site

all: data model luck

data:
	$(PY) src/run_01_build.py

model:
	$(PY) src/run_02_model.py

luck:
	$(PY) src/run_03_luck.py

# Regenerate the GitHub Pages page from README.md. Needs `pip install markdown`.
site:
	$(PY) tools/site.py

clean:
	rm -f figures/*.png output/*.csv data/processed/*
