#!/bin/bash

# Run the DataDotMD web application

echo "Starting DataDotMD server..."
uvicorn datadotmd.app.main:app --reload --host 0.0.0.0 --port 8000
