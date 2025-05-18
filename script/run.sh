#!/bin/bash

# Activate virtual environment if needed
# source venv/bin/activate

# Run the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload