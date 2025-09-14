.PHONY: help up down migrate superuser dev test lint clean

# Default target
help:
	@echo "ReferWell Direct - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make up          - Start Docker services (Postgres + Redis)"
	@echo "  make down        - Stop Docker services"
	@echo "  make migrate     - Run database migrations"
	@echo "  make superuser   - Create Django superuser"
	@echo "  make dev         - Start Django dev server + Celery worker"
	@echo "  make test        - Run test suite"
	@echo "  make lint        - Run pre-commit hooks"
	@echo "  make clean       - Clean up Docker volumes"
	@echo "  make shell       - Open Django shell"
	@echo "  make dbshell     - Open database shell"

# Start Docker services
up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started. Postgres: localhost:5432, Redis: localhost:6379"

# Stop Docker services
down:
	docker-compose down

# Run database migrations
migrate:
	python manage.py migrate

# Create Django superuser
superuser:
	python manage.py createsuperuser

# Start development server and Celery worker
dev:
	@echo "Starting Django development server and Celery worker..."
	@echo "Django: http://localhost:8000"
	@echo "Admin: http://localhost:8000/admin"
	@echo "Mailcatcher: http://localhost:1080"
	@echo ""
	@echo "Press Ctrl+C to stop both services"
	@echo ""
	@trap 'kill %1; kill %2' INT; \
	python manage.py runserver 0.0.0.0:8000 & \
	celery -A referwell worker --loglevel=info & \
	wait

# Run tests
test:
	python -m pytest

# Run tests with coverage
test-coverage:
	python -m pytest --cov=referwell --cov-report=html --cov-report=term

# Run specific test categories
test-models:
	python -m pytest tests/test_models.py

test-services:
	python -m pytest tests/test_services.py

test-views:
	python -m pytest tests/test_views.py

# Run linting
lint:
	pre-commit run --all-files

# Clean up Docker volumes
clean:
	docker-compose down -v
	docker system prune -f

# Django shell
shell:
	python manage.py shell

# Database shell
dbshell:
	python manage.py dbshell

# Collect static files
collectstatic:
	python manage.py collectstatic --noinput

# Load sample data
loaddata:
	python manage.py loaddata fixtures/sample_data.json

# Create new migration
makemigrations:
	python manage.py makemigrations

# Show migrations
showmigrations:
	python manage.py showmigrations

# Reset database (WARNING: destroys all data)
reset-db:
	@echo "WARNING: This will destroy all data in the database!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker-compose down -v
	docker-compose up -d
	sleep 10
	python manage.py migrate
	python manage.py createsuperuser
