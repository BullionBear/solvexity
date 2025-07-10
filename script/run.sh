#!/bin/bash

# Default config path
CONFIG=${1:-"config/config.yml"}

# Activate virtual environment if needed
# source venv/bin/activate
source script/env.sh
python -m solvexity.app.main --config $CONFIG
