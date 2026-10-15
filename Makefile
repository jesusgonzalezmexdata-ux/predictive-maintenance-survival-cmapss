PYTHON ?= python

.PHONY: help install lint test app figures docker
help:
	@echo "install lint test app figures docker"
install:
	$(PYTHON) -m pip install -r requirements-dev.txt
lint:
	ruff check .
test:
	$(PYTHON) -m pytest -q test/product
app:
	streamlit run app/streamlit_app.py
figures:
	$(PYTHON) tools/make_figures.py
docker:
	docker build -t pm-survival .
