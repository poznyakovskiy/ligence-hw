#!/bin/bash

PYTHONPATH=. venv/bin/python app/worker.py &
WORKER_PID=$!

venv/bin/uvicorn app.generator:app --port 8000 &
GENERATOR_PID=$!

venv/bin/uvicorn app.verifier:app --port 8001 &
VERIFIER_PID=$!

# Wait for both
wait $GENERATOR_PID $VERIFIER_PID $WORKER_PID