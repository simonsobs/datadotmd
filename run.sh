#!/bin/bash

# Run the DataDotMD web application

echo "Starting DataDotMD server..."
export DEBUG="yes"
uvicorn datadotmd.app.main:app --reload --host 0.0.0.0 --port 8000
