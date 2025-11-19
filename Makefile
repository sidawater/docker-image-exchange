.PHONY: help test test-unit test-cov install-test-deps

help:  ## Show this help
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-test-deps:  ## Install test dependencies
	pip install -r requirements-test.txt

test:  ## Run all tests
	pytest

test-unit:  ## Run only unit tests
	pytest -m unit -v

test-cov:  ## Run tests with coverage report
	pytest --cov=core --cov-report=term-missing --cov-report=html

test-schema:  ## Run schema tests only
	pytest tests/test_schema.py -v

test-file-api:  ## Run DocFile API tests only
	pytest tests/test_file_api.py -v

test-kminio:  ## Run MinIO client tests only
	pytest tests/test_kminio.py -v

test-knowledge:  ## Run Knowledge manager tests only
	pytest tests/test_knowledge.py -v

test-word-spliter:  ## Run WordSpliter tests only
	pytest tests/test_word_spliter.py -v

test-verbose:  ## Run tests with verbose output
	pytest -v --tb=short

test-fail-fast:  ## Run tests and stop on first failure
	pytest -x
