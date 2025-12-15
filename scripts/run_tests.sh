#!/bin/bash
# run_tests.sh - Comprehensive test execution script
#
# Usage:
#   ./scripts/run_tests.sh [options]
#
# Options:
#   --unit              Run only unit tests
#   --integration       Run only integration tests
#   --coverage          Generate coverage report
#   --html              Generate HTML coverage report
#   --fast              Run tests in parallel (requires pytest-xdist)
#   --verbose           Verbose output
#   --docker            Run tests in Docker environment
#   --ci                CI mode (used in CI/CD pipelines)
#   --help              Show this help message

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_ALL=true
COVERAGE=false
HTML_REPORT=false
PARALLEL=false
VERBOSE=false
DOCKER=false
CI_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            COVERAGE=true
            shift
            ;;
        --fast)
            PARALLEL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --docker)
            DOCKER=true
            shift
            ;;
        --ci)
            CI_MODE=true
            COVERAGE=true
            shift
            ;;
        --help)
            echo "Usage: ./scripts/run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --unit              Run only unit tests"
            echo "  --integration       Run only integration tests"
            echo "  --coverage          Generate coverage report"
            echo "  --html              Generate HTML coverage report"
            echo "  --fast              Run tests in parallel"
            echo "  --verbose           Verbose output"
            echo "  --docker            Run tests in Docker environment"
            echo "  --ci                CI mode (coverage + strict)"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print banner
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Speech-to-Text Service Test Runner${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run tests in Docker
run_tests_docker() {
    echo -e "${YELLOW}Running tests in Docker environment...${NC}"
    
    # Start test services
    docker-compose -f docker-compose.test.yml up -d test-db test-redis
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5
    
    # Run tests in container
    docker-compose -f docker-compose.test.yml run --rm test-runner
    
    # Stop and clean up
    docker-compose -f docker-compose.test.yml down -v
    
    echo -e "${GREEN}Docker tests completed!${NC}"
    exit 0
}

# If Docker mode, run tests in Docker and exit
if [ "$DOCKER" = true ]; then
    run_tests_docker
fi

# Check for pytest
if ! command_exists pytest; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install -e .[dev]"
    exit 1
fi

# Load test environment variables
if [ -f .env.test ]; then
    echo -e "${YELLOW}Loading test environment variables...${NC}"
    export $(grep -v '^#' .env.test | xargs)
fi

# Build pytest command
PYTEST_CMD="pytest"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    if command_exists pytest-xdist; then
        echo -e "${YELLOW}Running tests in parallel...${NC}"
        PYTEST_CMD="$PYTEST_CMD -n auto"
    else
        echo -e "${YELLOW}Warning: pytest-xdist not installed, running sequentially${NC}"
    fi
fi

# Add coverage options
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term-missing"
    
    if [ "$HTML_REPORT" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
    
    if [ "$CI_MODE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=xml --cov-fail-under=80"
    fi
fi

# Add test selection markers
if [ "$RUN_UNIT" = true ]; then
    echo -e "${YELLOW}Running unit tests only...${NC}"
    PYTEST_CMD="$PYTEST_CMD -m unit"
elif [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${YELLOW}Running integration tests only...${NC}"
    PYTEST_CMD="$PYTEST_CMD -m integration"
elif [ "$RUN_ALL" = true ]; then
    echo -e "${YELLOW}Running all tests...${NC}"
fi

# Check Redis availability for integration tests
if [ "$RUN_INTEGRATION" = true ] || [ "$RUN_ALL" = true ]; then
    if command_exists redis-cli; then
        if ! redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
            echo -e "${YELLOW}Warning: Redis is not running. Integration tests may fail.${NC}"
            echo -e "${YELLOW}Start Redis with: redis-server${NC}"
        fi
    fi
fi

# Print test command
echo -e "${BLUE}Test command:${NC} $PYTEST_CMD"
echo ""

# Run tests
echo -e "${GREEN}Starting tests...${NC}"
echo ""

if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    # Show coverage report location if generated
    if [ "$HTML_REPORT" = true ]; then
        echo -e "${GREEN}HTML coverage report: htmlcov/index.html${NC}"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
