#!/bin/bash

# Function to start Docker Compose
init() {
    echo "Starting Docker Compose..."
    docker compose up logger spot_feed -d
}

# Function to stop Docker Compose
stop() {
    echo "Stopping Docker Compose..."
    docker compose down spot_feed logger
}

# Function to clean up Docker artifacts
clean() {
    echo "Cleaning up Docker artifacts..."
    rm -rf log/*
    rm -rf verbose/*
    echo "Cleanup complete."
}

# Display usage information
usage() {
    echo "Usage: $0 {run|stop|clean}"
    exit 1
}

# Check if a command is provided
if [[ $# -lt 1 ]]; then
    usage
fi

# Process the command
case "$1" in
    run)
        run
        ;;
    stop)
        stop
        ;;
    clean)
        clean
        ;;
    *)
        echo "Error: Invalid command '$1'"
        usage
        ;;
esac