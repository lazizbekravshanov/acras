.PHONY: setup seed demo dev test lint clean

# One-command setup
setup:
	cp -n .env.example .env 2>/dev/null || true
	docker compose build

# Start all services
dev:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Seed the database with camera feeds
seed:
	docker compose exec backend python -m scripts.seed_cameras

# Generate sample incident data for demos
sample-data:
	docker compose exec backend python -m scripts.generate_sample_data --count 1000

# Full demo: start everything + seed + sample data
demo: setup
	docker compose up -d
	@echo "Waiting for services to start..."
	@sleep 10
	docker compose exec backend python -m scripts.seed_cameras
	docker compose exec backend python -m scripts.generate_sample_data --count 1000
	@echo ""
	@echo "ACRAS is running!"
	@echo "  Dashboard: http://localhost:3000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Grafana:   http://localhost:3001 (admin/admin)"

# Run backend tests
test:
	cd backend && python -m pytest tests/ -v --tb=short

# Run linting
lint:
	cd backend && python -m ruff check app/ tests/

# Run database migrations
migrate:
	docker compose exec backend alembic upgrade head

# Create a new migration
migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# Simulate a camera feed
simulate:
	docker compose exec backend python -m scripts.simulate_feed --duration 300

# View logs
logs:
	docker compose logs -f backend celery_worker

# Clean up everything
clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
