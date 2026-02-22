#!/bin/bash
# Quick dev startup script for SaaS Factory
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting SaaS Factory development environment..."

# Start infrastructure
echo "Starting PostgreSQL + Redis..."
docker compose up postgres redis -d

echo "Waiting for PostgreSQL to be ready..."
for i in {1..20}; do
    if docker compose exec -T postgres pg_isready -U saas >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Backend
echo "Starting FastAPI backend on :8001..."
cd "$SCRIPT_DIR/backend"
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating Python venv..."
    python3 -m venv "$SCRIPT_DIR/.venv"
    "$SCRIPT_DIR/.venv/bin/pip" install -r requirements.txt -q
fi
"$SCRIPT_DIR/.venv/bin/uvicorn" main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# Frontend
echo "Starting Next.js frontend on :3000..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install --legacy-peer-deps
fi
npm run dev &
FRONTEND_PID=$!

echo ""
echo "SaaS Factory running:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8001"
echo "  API Docs:  http://localhost:8001/docs"
echo "  AI Status: http://localhost:8001/api/v1/ai/status"
echo ""
echo "Press Ctrl+C to stop all services"

cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    docker compose stop postgres redis
    exit 0
}
trap cleanup INT TERM

wait
