#!/bin/bash

# Default config path
CONFIG=${CONFIG:-"solvexity/config/config.yml"}

# Activate virtual environment if needed
# source venv/bin/activate

python -m solvexity.app.main --config $CONFIG
