#!/bin/bash
# Convenience script to run tests with all environment variables

# Check if dependencies are installed
if ! python3 -c "import pydantic_settings" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -q -r requirements-test.txt 2>&1 | grep -E "(Successfully installed|ERROR)" || true
    echo "Dependencies installed!"
    echo ""
fi

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=prowl_user
export POSTGRES_PASSWORD=prowl_password
export POSTGRES_DB=prowl_db
export OPENROUTER_API_KEY=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
export OPENROUTER_BASE=https://openrouter.ai/api/v1

# Run tests
python3 test_kg_index.py
