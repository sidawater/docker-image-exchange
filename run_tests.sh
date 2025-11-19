#!/bin/bash
# Test runner script for the project

set -e

echo "======================================"
echo "Running Unit Tests for Core Module"
echo "======================================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed"
    echo "Install with: pip install -r requirements-test.txt"
    exit 1
fi

# Run tests with coverage
echo "Running tests with coverage..."
pytest --cov=core --cov-report=term-missing --cov-report=html

echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo ""
echo "Coverage report generated in htmlcov/"
echo "Open htmlcov/index.html to view detailed coverage"
