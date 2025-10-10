#!/bin/bash

# Shell script to visualize all dataframe CSV files using ohlcv_visualizer.py
# This script activates the virtual environment and processes all dataframe_*.csv files

set -e  # Exit on any error

echo "Starting OHLCV visualization for all dataframe files..."

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if we're in the virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "✗ Failed to activate virtual environment"
    exit 1
fi

# Create charts directory if it doesn't exist
mkdir -p charts

# Count total files
total_files=$(ls dataframe_*.csv 2>/dev/null | wc -l)
if [ $total_files -eq 0 ]; then
    echo "No dataframe_*.csv files found!"
    exit 1
fi

echo "Found $total_files dataframe CSV files to process"

# Process each dataframe CSV file
counter=0
successful=0
failed=0

for csv_file in dataframe_*.csv; do
    counter=$((counter + 1))
    
    # Extract timestamp from filename
    timestamp=$(echo "$csv_file" | sed 's/dataframe_\(.*\)\.csv/\1/')
    output_file="charts/ohlcv_${timestamp}.png"
    
    echo "[$counter/$total_files] Processing: $csv_file -> $output_file"
    
    # Run the OHLCV visualizer
    if python alpha/ohlcv_visualizer.py --input "$csv_file" --output "$output_file" --format png; then
        echo "  ✓ Successfully created $output_file"
        successful=$((successful + 1))
    else
        echo "  ✗ Failed to create $output_file"
        failed=$((failed + 1))
    fi
done

# Summary
echo ""
echo "Batch processing complete!"
echo "Successfully processed: $successful files"
echo "Failed: $failed files"
echo "Charts saved to: charts/"

if [ $failed -gt 0 ]; then
    exit 1
fi
