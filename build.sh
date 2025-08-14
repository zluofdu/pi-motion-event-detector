#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔨 Starting build process..."

# Check for virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}⚠️  No virtual environment detected!${NC}"
    echo "Creating a new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install project and development dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests with coverage and verbose output
echo "🧪 Running tests..."
PYTHONPATH=. python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Check the test result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi

# Clean up previous builds
echo "🧹 Cleaning up previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build the package
echo "📦 Building package..."
python -m build

# Run twine check
echo "🔍 Checking distribution files..."
twine check dist/*

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build successful! Distribution files are ready in ./dist/${NC}"
else
    echo -e "${RED}❌ Build check failed!${NC}"
    exit 1
fi

# List the contents of dist directory
echo "📁 Generated distribution files:"
ls -l dist/
