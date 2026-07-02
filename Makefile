.PHONY: install api web seed test lint eval demo-report reset docker

install:            ## Install backend + frontend dependencies
	pip install -r apps/api/requirements.txt
	cd apps/web && npm install

api:                ## Run the FastAPI backend on :8000
	cd apps/api && uvicorn app.main:app --reload --port 8000

web:                ## Run the Next.js frontend on :3000
	cd apps/web && npm run dev

seed:               ## Load synthetic demo data (idempotent)
	python3 scripts/seed_data.py

reset:              ## Wipe and reseed the demo database
	python3 scripts/seed_data.py --reset

test:               ## Backend unit + integration tests
	cd apps/api && python3 -m pytest

lint:               ## Frontend lint + build type-check
	cd apps/web && npm run lint && npm run build

eval:               ## Run the detection evaluation (writes data/evaluation/results.*)
	python3 scripts/evaluate.py

demo-report:        ## Generate a sample evidence PDF from the seeded critical case
	python3 scripts/generate_demo_report.py

docker:             ## Full stack via Docker Compose
	docker compose up --build
