#!/bin/bash
# Setup script for RAG service local development

echo "Setting up RAG Service..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

echo ""
echo "Setup complete!"
echo ""
echo "To run the service locally:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Set environment variables (or copy .env.example to .env)"
echo "3. Run: python main.py"
echo ""
echo "To run with Docker:"
echo "docker-compose up -d rag_service"
