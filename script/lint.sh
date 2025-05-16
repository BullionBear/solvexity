#!/bin/bash
# Script to run all linters on the ./solvexity directory

set -e  # Exit immediately if a command exits with a non-zero status

TARGET_DIR="./solvexity"

echo "Running black..."
black ${TARGET_DIR}

echo "Running isort..."
isort ${TARGET_DIR}

echo "Running flake8..."
flake8 ${TARGET_DIR}

echo "Running pylint..."
pylint ${TARGET_DIR}

echo "Running mypy..."
mypy ${TARGET_DIR}

echo "All linting completed successfully!"
