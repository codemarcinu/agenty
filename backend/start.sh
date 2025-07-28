#!/bin/bash

# --- AUTO FREE PORT 8000 ---
PORT=8000
if lsof -i :$PORT &>/dev/null; then
  echo "[INFO] Port $PORT zajęty. Zwalniam..."
  PID=$(lsof -ti :$PORT)
  kill -9 $PID
  echo "[INFO] Port $PORT został zwolniony (PID: $PID)"
else
  echo "[INFO] Port $PORT jest wolny."
fi

# --- START BACKEND (FastAPI/uvicorn) ---

# Możesz dodać tu własne zmienne środowiskowe, np.:
# export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/foodsave

exec uvicorn backend.app_factory:app --host 0.0.0.0 --port 8000 --reload
