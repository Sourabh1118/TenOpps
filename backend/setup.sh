#!/bin/bash
# Setup script for backend development environment

set -e

echo "Setting up Job Aggregation Platform Backend..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

echo ""
echo "Setup complete! Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start PostgreSQL and Redis"
echo "3. Run migrations: alembic upgrade head"
echo "4. Start the server: python app/main.py"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
