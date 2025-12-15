#!/bin/bash
# Test runner script for the Speech-to-Text service

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Speech-to-Text Service Test Suite ===${NC}\n"

# Parse command line arguments
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

# Function to run tests
run_tests() {
    local marker="$1"
    local description="$2"
    
    echo -e "${YELLOW}Running $description...${NC}"
    
    if [ "$marker" = "all" ]; then
        if [ "$VERBOSE" = "-v" ] || [ "$VERBOSE" = "--verbose" ]; then
            pytest -v
        else
            pytest
        fi
    else
        if [ "$VERBOSE" = "-v" ] || [ "$VERBOSE" = "--verbose" ]; then
            pytest -m "$marker" -v
        else
            pytest -m "$marker"
        fi
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $description passed${NC}\n"
    else
        echo -e "${RED}✗ $description failed${NC}\n"
        exit 1
    fi
}

# Display usage
if [ "$TEST_TYPE" = "-h" ] || [ "$TEST_TYPE" = "--help" ]; then
    echo "Usage: ./run_tests.sh [test-type] [options]"
    echo ""
    echo "Test Types:"
    echo "  all              Run all tests (default)"
    echo "  unit             Run only unit tests"
    echo "  integration      Run only integration tests"
    echo "  auth             Run authentication tests"
    echo "  lexicon          Run lexicon service tests"
    echo "  text             Run text processing tests"
    echo "  numerals         Run numeral conversion tests"
    echo "  coverage         Run tests with coverage report"
    echo ""
    echo "Options:"
    echo "  -v, --verbose    Run tests in verbose mode"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh                  # Run all tests"
    echo "  ./run_tests.sh unit             # Run unit tests only"
    echo "  ./run_tests.sh auth -v          # Run auth tests verbosely"
    echo "  ./run_tests.sh coverage         # Run with coverage report"
    exit 0
fi

# Run appropriate tests based on type
case "$TEST_TYPE" in
    all)
        run_tests "all" "All Tests"
        ;;
    unit)
        run_tests "unit" "Unit Tests"
        ;;
    integration)
        run_tests "integration" "Integration Tests"
        ;;
    auth)
        run_tests "auth" "Authentication Tests"
        ;;
    lexicon)
        run_tests "lexicon" "Lexicon Service Tests"
        ;;
    text)
        run_tests "text_processing" "Text Processing Tests"
        ;;
    numerals)
        run_tests "numerals" "Numeral Conversion Tests"
        ;;
    coverage)
        echo -e "${YELLOW}Running tests with coverage...${NC}"
        pytest --cov=app --cov-report=html --cov-report=term-missing
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Coverage report generated${NC}"
            echo -e "${YELLOW}HTML report: htmlcov/index.html${NC}\n"
        else
            echo -e "${RED}✗ Coverage generation failed${NC}\n"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Run './run_tests.sh --help' for usage information"
        exit 1
        ;;
esac

echo -e "${GREEN}=== All requested tests passed! ===${NC}"
