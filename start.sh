#!/usr/bin/env bash
set -e
cd backend
python -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!
cd ../frontend
npm install
npm run dev &
FRONT_PID=$!
echo "AION backend: http://localhost:8000"
echo "AION frontend: http://localhost:5173"
wait $BACK_PID $FRONT_PID
