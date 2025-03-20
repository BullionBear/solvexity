#!/bin/bash
set -xe
PROTO_DIR="./proto"
OUT_DIR="solvexity/generated"

# Function to start Docker Compose
codegen() {
    echo "Generate pb2 grpc from proto..."
    # Loop through each .proto file and generate Python files
    for proto_file in "$PROTO_DIR"/*.proto; do
        proto_name=$(basename "$proto_file" .proto)
        proto_out_dir="$OUT_DIR/$proto_name"
        mkdir -p "$proto_out_dir"
        
        echo "Generating files for $proto_file..."
        python -m grpc_tools.protoc -I="$PROTO_DIR" --python_out="$proto_out_dir" --grpc_python_out="$proto_out_dir" "$proto_file"
    done
    
    # Fix imports in *_pb2_grpc.py files
    for grpc_file in "$OUT_DIR"/*/*_pb2_grpc.py; do
        echo "Fixing imports in $grpc_file..."
        sed -i 's/import \(.*_pb2\) as/from . import \1 as/' "$grpc_file"
    done
}

clean() {
    echo "Cleaning up generated files..."
    # Remove generated files except __init__.py
    find solvexity/generated -type f -not -name '__init__.py' -delete
}


# Display usage information
usage() {
    echo "Usage: $0 {codegen|clean}"
    exit 1
}

# Check if a command is provided
if [[ $# -lt 1 ]]; then
    usage
fi

# Process the command
case "$1" in
    codegen)
        codegen
        ;;
    clean)
        clean
        ;;
    *)
        echo "Error: Invalid command '$1'"
        usage
        ;;
esac

