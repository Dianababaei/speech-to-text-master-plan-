#!/bin/bash
# Script to run integration tests with isolated test environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting integration test environment...${NC}"

# Start test services
echo "Starting PostgreSQL and Redis test containers..."
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Check if services are healthy
if ! docker-compose -f docker-compose.test.yml ps | grep -q "Up"; then
    echo -e "${RED}Error: Test services failed to start${NC}"
    docker-compose -f docker-compose.test.yml logs
    docker-compose -f docker-compose.test.yml down
    exit 1
fi

echo -e "${GREEN}Test services are ready${NC}"

# Set test environment variables
export TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_transcription"
export TEST_REDIS_URL="redis://localhost:6380/0"

# Run tests
echo -e "${GREEN}Running integration tests...${NC}"
if pytest tests/integration/ -v "$@"; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    TEST_RESULT=0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    TEST_RESULT=1
fi

# Cleanup
echo -e "${YELLOW}Stopping test services...${NC}"
docker-compose -f docker-compose.test.yml down

exit $TEST_RESULT
