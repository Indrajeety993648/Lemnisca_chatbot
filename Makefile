.PHONY: install test run-backend run-frontend ingest help

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	pytest tests/backend
	cd frontend && npm test

run-backend:
	python -m backend.main

run-frontend:
	cd frontend && npm run dev

ingest:
	python scripts/ingest_all_pdfs.py

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies for backend and frontend"
	@echo "  make test         - Run tests for backend and frontend"
	@echo "  make run-backend  - Start the FastAPI backend"
	@echo "  make run-frontend - Start the Vite frontend"
	@echo "  make ingest       - Run the batch PDF ingestion script"
