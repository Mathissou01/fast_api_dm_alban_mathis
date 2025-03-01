#!/bin/sh

# Activate the virtual environment
source .venv/bin/activate

# Run database.py to initialize the database
python database.py

# Run dbseeder.py to seed the database
python dbseeder.py

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000
