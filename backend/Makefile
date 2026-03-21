.PHONY: help install run test clean migrate worker beat flower celery-test

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make migrate      - Run database migrations"
	@echo "  make worker       - Start Celery worker"
	@echo "  make beat         - Start Celery beat scheduler"
	@echo "  make flower       - Start Celery Flower monitoring"
	@echo "  make celery-test  - Test Celery configuration"
	@echo "  make clean        - Remove cache and build files"

install:
	pip install -r requirements.txt

run:
	python app/main.py

test:
	pytest

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

migrate:
	alembic upgrade head

worker:
	./scripts/run_celery_worker.sh

beat:
	./scripts/run_celery_beat.sh

flower:
	./scripts/run_celery_flower.sh

celery-test:
	python scripts/test_celery.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -f celerybeat-schedule
	rm -f celerybeat.pid
