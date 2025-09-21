#!/bin/bash

# Proto generation script for solvexity
# This script generates Python protobuf files from .proto definitions

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Starting protobuf generation...${NC}"

# Check if protoc is available
if ! command -v protoc &> /dev/null; then
    echo -e "${RED}Error: protoc compiler not found. Please install Protocol Buffers compiler.${NC}"
    echo "On Ubuntu/Debian: sudo apt-get install protobuf-compiler"
    echo "On macOS: brew install protobuf"
    exit 1
fi

# Check if protobuf Python package is installed
if ! python -c "import google.protobuf" 2>/dev/null; then
    echo -e "${RED}Error: protobuf Python package not found.${NC}"
    echo "Please install it with: pip install protobuf"
    exit 1
fi

# Define directories
PROTO_DIR="$PROJECT_ROOT/protobuf"
OUTPUT_DIR="$PROJECT_ROOT/solvexity/model/protobuf"

# Check if proto directory exists
if [ ! -d "$PROTO_DIR" ]; then
    echo -e "${RED}Error: Protobuf directory not found at $PROTO_DIR${NC}"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Find all .proto files
PROTO_FILES=$(find "$PROTO_DIR" -name "*.proto" -type f)

if [ -z "$PROTO_FILES" ]; then
    echo -e "${RED}Error: No .proto files found in $PROTO_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}Found proto files:${NC}"
for file in $PROTO_FILES; do
    echo "  - $(basename "$file")"
done

# Generate Python files
echo -e "${YELLOW}Generating Python protobuf files...${NC}"

# Change to project root for proper imports
cd "$PROJECT_ROOT"

# Generate protobuf files
for proto_file in $PROTO_FILES; do
    echo "Processing $(basename "$proto_file")..."
    protoc \
        --proto_path="$PROJECT_ROOT" \
        --python_out="$OUTPUT_DIR" \
        "$proto_file"
done

# Move files from nested protobuf directory if they were created there
if [ -d "$OUTPUT_DIR/protobuf" ]; then
    echo "Moving files from nested protobuf directory..."
    mv "$OUTPUT_DIR/protobuf"/*.py "$OUTPUT_DIR/"
    rmdir "$OUTPUT_DIR/protobuf"
fi

# Create __init__.py files to make directories Python packages
echo "# Generated protobuf modules" > "$OUTPUT_DIR/__init__.py"

# Fix import paths in generated files
echo -e "${YELLOW}Fixing import paths in generated files...${NC}"
for py_file in "$OUTPUT_DIR"/*.py; do
    if [[ -f "$py_file" && "$(basename "$py_file")" != "__init__.py" ]]; then
        # Fix relative imports
        sed -i 's/from protobuf import \([^[:space:]]*\) as/from . import \1 as/g' "$py_file"
        echo "Fixed imports in $(basename "$py_file")"
    fi
done

# Add imports to __init__.py for easier access
echo -e "${YELLOW}Adding imports to __init__.py...${NC}"
cat >> "$OUTPUT_DIR/__init__.py" << 'EOF'

# Import all generated protobuf modules
try:
    from .shared_pb2 import *
    from .trade_pb2 import *
except ImportError as e:
    print(f"Warning: Could not import protobuf modules: {e}")

# Re-export common classes for easier access
__all__ = [
    # Enums from shared.proto
    'Instrument', 'Exchange', 'Side', 'TimeInForce', 'OrderType',
    # Messages from shared.proto
    'Symbol',
    # Messages from trade.proto
    'Trade',
]
EOF

echo -e "${GREEN}✓ Protobuf generation completed successfully!${NC}"
echo -e "${GREEN}Generated files in: $OUTPUT_DIR${NC}"

# List generated files
echo -e "${YELLOW}Generated files:${NC}"
find "$OUTPUT_DIR" -name "*.py" -type f | while read -r file; do
    echo "  - $(basename "$file")"
done

echo -e "${GREEN}✓ Done!${NC}"
