#!/bin/bash

# Function to center text with a specified padding character
center_text() {
    local text="$1"
    local padding_char="$2"
    local width=$(tput cols)
    local text_length=${#text}
    local padding=$(( (width - text_length) / 2 - 2 ))
    echo ""
    printf '%*s%s%*s\n' "$padding" ' ' "$text" "$padding" ' ' | tr ' ' "$padding_char"
    echo ""
}

center_text "Running Unit Tests" "="

echo "Navigating to test modules..."
cd "$(dirname "$0")/dags/unibas/test" || { echo "Failed to navigate to the test modules."; exit 1; }
echo "Navigated to $PWD"

echo "Checking that we are in a virtual environment..."
if [ -z "$VIRTUAL_ENV" ]; then
    echo "- You are not in a virtual environment. Please source the venv."
    echo "- Run \"source .venv/bin/activate\" in your terminal."
    exit 1
fi

echo "Checking that pytest is installed..."
if ! command -v pytest &> /dev/null; then
    echo "pytest is not installed. Installing pytest..."
    pip install pytest
fi

echo "Running pytest..."
pytest
EXIT_CODE=$?

echo "Checking pytest exit code..."
if [ $EXIT_CODE -ne 0 ]; then
    echo "$EXIT_CODE: Tests failed"
    exit 1
else
    echo "Done. All tests passed."
    exit 0
fi