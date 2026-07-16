.PHONY: dev backend frontend test lint build docker clean

# Development
dev:
	@echo "Starting infrastructure (postgres + redis)..."
	docker compose up -d postgres redis
	@echo "Start backend: make backend"
	@echo "Start frontend: make frontend"

backend:
	cd backend && uv run uvicorn stromwart.app:app --reload --port 8000

frontend:
	cd frontend && npm run dev

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest tests/ -v

test-frontend:
	cd frontend && npx playwright test

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check src/ scripts/
	cd backend && uv run mypy --strict src/stromwart/

lint-frontend:
	cd frontend && npx tsc --noEmit

# Build
build:
	cd frontend && npm run build

# Docker
docker:
	docker compose config

docker-up:
	docker compose up -d

docker-down:
	docker compose down

# ML
train:
	cd backend && uv run python scripts/generate_synthetic_data.py
	cd backend && uv run python scripts/train_models.py

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .venv -exec rm -rf {} + 2>/dev/null || true
