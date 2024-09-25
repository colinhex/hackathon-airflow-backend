#!/bin/bash

# Navigate to the directory of the script
cd "$("./dags/unibas/common/test")" || exit

# Check if we are in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "You are not in a virtual environment. Please source the venv."
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest is not installed. Installing pytest..."
    pip install pytest
fi

# Check if pytest-sugar is installed
if ! pip show pytest-sugar &> /dev/null; then
    echo "pytest-sugar is not installed. Installing pytest-sugar..."
    pip install pytest-sugar
fi

# Run pytest
pytest