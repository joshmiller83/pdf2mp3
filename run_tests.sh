#!/bin/bash
# Test runner script for pdf2txt project

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PDF2TXT Test Runner${NC}"
echo "===================="
echo

# Check if virtual environment exists
if [ -d "mlx310" ]; then
    echo -e "${GREEN}✓${NC} Found virtual environment: mlx310"
    source mlx310/bin/activate
elif [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Found virtual environment: venv"
    source venv/bin/activate
else
    echo -e "${YELLOW}!${NC} No virtual environment found. Using system Python."
    echo "  Recommended: Create a virtual environment first:"
    echo "  python3 -m venv venv && source venv/bin/activate"
    echo
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${RED}✗${NC} pytest is not installed"
    echo "  Installing pytest..."
    pip install pytest pytest-asyncio
    echo
fi

# Run tests
echo -e "${GREEN}Running tests...${NC}"
echo

# Run with different options based on arguments
if [ "$1" = "-v" ] || [ "$1" = "--verbose" ]; then
    python -m pytest tests/ -v
elif [ "$1" = "-vv" ]; then
    python -m pytest tests/ -vv --tb=long
elif [ "$1" = "--cov" ]; then
    python -m pytest tests/ --cov=. --cov-report=html --cov-report=term
elif [ "$1" = "--help" ]; then
    echo "Usage: ./run_tests.sh [option]"
    echo
    echo "Options:"
    echo "  (none)      Run all tests with standard output"
    echo "  -v          Run with verbose output"
    echo "  -vv         Run with very verbose output and full tracebacks"
    echo "  --cov       Run with coverage report (requires pytest-cov)"
    echo "  --help      Show this help message"
    echo
    echo "Examples:"
    echo "  ./run_tests.sh              # Run all tests"
    echo "  ./run_tests.sh -v           # Verbose output"
    echo "  ./run_tests.sh --cov        # With coverage"
    echo
else
    python -m pytest tests/ --tb=short
fi

# Capture exit code
EXIT_CODE=$?

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

exit $EXIT_CODE
