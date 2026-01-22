#!/bin/bash
# =============================================================================
# EdTech Word Chain Game - Production Startup Script
# =============================================================================
# Usage: ./run_production.sh
#
# This script starts the FastAPI application with production-optimized settings
# using Gunicorn with Uvicorn workers for high concurrency.
# =============================================================================

set -e

# Default settings (can be overridden by environment variables)
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  EdTech Word Chain API - Production${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Not running in a virtual environment${NC}"
    echo "Consider activating your venv first: source .venv/bin/activate"
    echo ""
fi

# Check for required environment variables
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" == "your-super-secret-key-change-in-production" ]; then
    echo -e "${RED}ERROR: SECRET_KEY is not set or using default value!${NC}"
    echo "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    exit 1
fi

# Display configuration
echo -e "Configuration:"
echo -e "  Host:    ${GREEN}$HOST${NC}"
echo -e "  Port:    ${GREEN}$PORT${NC}"
echo -e "  Workers: ${GREEN}$WORKERS${NC}"
echo -e "  Log Level: ${GREEN}$LOG_LEVEL${NC}"
echo ""

# Check if we should use workers (production) or single process (development)
if [ "$WORKERS" == "1" ]; then
    echo -e "${GREEN}Starting Uvicorn (single worker)...${NC}"
    exec uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$LOG_LEVEL"
else
    echo -e "${GREEN}Starting Uvicorn with $WORKERS workers...${NC}"
    exec uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level "$LOG_LEVEL"
fi
