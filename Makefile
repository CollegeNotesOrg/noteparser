.PHONY: help build up down logs shell test clean install dev prod init-services

# Variables
COMPOSE_FILE = docker-compose.yml
COMPOSE_DEV_FILE = docker-compose.dev.yml
PROJECT_NAME = noteparser

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

build: ## Build Docker images
	docker-compose -f $(COMPOSE_FILE) build

build-dev: ## Build development Docker images
	docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) build

up: ## Start all services
	docker-compose -f $(COMPOSE_FILE) up -d

up-dev: ## Start all services in development mode
	docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) up -d

down: ## Stop all services
	docker-compose -f $(COMPOSE_FILE) down

down-clean: ## Stop all services and remove volumes
	docker-compose -f $(COMPOSE_FILE) down -v

logs: ## View logs from all services
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-service: ## View logs from specific service (usage: make logs-service SERVICE=noteparser)
	docker-compose -f $(COMPOSE_FILE) logs -f $(SERVICE)

shell: ## Open shell in noteparser container
	docker-compose -f $(COMPOSE_FILE) exec noteparser /bin/bash

shell-service: ## Open shell in specific service (usage: make shell-service SERVICE=postgres)
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE) /bin/sh

test: ## Run tests
	docker-compose -f $(COMPOSE_FILE) exec noteparser pytest tests/ -v

test-local: ## Run tests locally
	pytest tests/ -v --cov=noteparser

lint: ## Run linting
	black src/
	ruff check src/
	mypy src/noteparser/

format: ## Format code
	black src/ tests/
	ruff check --fix src/ tests/

clean: ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

init-services: ## Initialize AI services
	@echo "Initializing AI services..."
	docker-compose -f $(COMPOSE_FILE) up -d postgres redis elasticsearch
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Setting up Kong API Gateway..."
	docker-compose -f $(COMPOSE_FILE) up -d kong-db
	@sleep 5
	docker-compose -f $(COMPOSE_FILE) exec kong-db psql -U kong -c "CREATE DATABASE kong;" || true
	docker-compose -f $(COMPOSE_FILE) run --rm kong kong migrations bootstrap
	docker-compose -f $(COMPOSE_FILE) up -d kong
	@echo "Loading Kong configuration..."
	@sleep 5
	curl -i -X POST http://localhost:8001/config -F config=@gateway/kong.yml
	@echo "Services initialized successfully!"

health-check: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:5000/health | jq '.' || echo "Noteparser: DOWN"
	@echo "Checking AI services via CLI..."
	@python -m noteparser.cli ai health || echo "AI services health check failed"
	@echo ""

ai-dev: ## Start development with AI services
	@echo "Starting AI services..."
	@if [ ! -d "../noteparser-ai-services" ]; then \
		echo "Error: noteparser-ai-services repository not found"; \
		echo "Please clone it: git clone https://github.com/CollegeNotesOrg/noteparser-ai-services.git"; \
		exit 1; \
	fi
	cd ../noteparser-ai-services && docker-compose up -d
	@echo "Waiting for AI services to start..."
	@sleep 15
	@echo "Starting noteparser..."
	make up-dev
	@echo "Testing AI integration..."
	make health-check

ai-test: ## Test AI integration
	@echo "Testing AI integration..."
	@python -c "import asyncio; from src.noteparser.integration.service_client import ServiceClientManager; print('✅ ServiceClientManager import successful')"
	@python -c "import asyncio; from src.noteparser.integration.ai_services import AIServicesIntegration; print('✅ AIServicesIntegration import successful')"

ai-stop: ## Stop all AI services
	@echo "Stopping AI services..."
	@if [ -d "../noteparser-ai-services" ]; then \
		cd ../noteparser-ai-services && docker-compose down; \
	fi
	make down

monitor: ## Open monitoring dashboards
	@echo "Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Jaeger: http://localhost:16686"
	@echo "Kibana: http://localhost:5601"

dev: build-dev up-dev logs ## Full development setup

prod: build up ## Production setup

restart: down up ## Restart all services

restart-service: ## Restart specific service (usage: make restart-service SERVICE=noteparser)
	docker-compose -f $(COMPOSE_FILE) restart $(SERVICE)

ps: ## Show running services
	docker-compose -f $(COMPOSE_FILE) ps

stats: ## Show container statistics
	docker stats --no-stream

backup: ## Backup databases
	@echo "Backing up databases..."
	@mkdir -p backups
	docker-compose -f $(COMPOSE_FILE) exec postgres pg_dump -U noteparser noteparser > backups/postgres_$$(date +%Y%m%d_%H%M%S).sql
	docker-compose -f $(COMPOSE_FILE) exec redis redis-cli BGSAVE
	@echo "Backup completed!"

restore: ## Restore databases from backup (usage: make restore BACKUP_FILE=backups/postgres_20240101_120000.sql)
	@echo "Restoring from $(BACKUP_FILE)..."
	docker-compose -f $(COMPOSE_FILE) exec -T postgres psql -U noteparser noteparser < $(BACKUP_FILE)
	@echo "Restore completed!"

migrate: ## Run database migrations
	docker-compose -f $(COMPOSE_FILE) exec noteparser python -m noteparser.db.migrate

seed: ## Seed database with sample data
	docker-compose -f $(COMPOSE_FILE) exec noteparser python -m noteparser.db.seed

api-docs: ## Generate API documentation
	docker-compose -f $(COMPOSE_FILE) exec noteparser python -m noteparser.docs.generate

version: ## Show version information
	@echo "NoteParser Version: $$(grep version pyproject.toml | head -1 | cut -d'"' -f2)"
	@echo "Docker Compose Version: $$(docker-compose --version)"
	@echo "Docker Version: $$(docker --version)"