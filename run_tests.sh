#!/bin/bash

# Exit on any error
set -e

# Set up environment variables for testing (if needed)
export TESTING=true

# Run all tests
echo "Running all tests..."
python -m pytest tests/

# Run specific test categories
echo "Running API tests..."
python -m pytest tests/api/

echo "Running service tests..."
python -m pytest tests/services/

# Run with coverage (if pytest-cov is installed)
if pip list | grep -q pytest-cov; then
  echo "Running tests with coverage..."
  python -m pytest --cov=app tests/
  python -m pytest --cov=app --cov-report=html tests/
  echo "Coverage report generated in htmlcov/ directory"
fi

echo "All tests completed!"
