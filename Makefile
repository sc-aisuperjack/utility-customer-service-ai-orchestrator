.PHONY: install run test eval smoke

install:
	python -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --port 8001

test:
	pytest -q

eval:
	python -m evals.run_evals

smoke:
	python scripts/smoke_test.py
