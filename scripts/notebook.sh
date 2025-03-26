#!/bin/bash

# Exit immediately if any command fails
set -e

# Strip outputs from all .ipynb files recursively under ./notebook
find ./notebooks -type f -name "*.ipynb" -print0 | while IFS= read -r -d '' file; do
    echo "Stripping: $file"
    nbstripout "$file"
done

echo "All notebooks stripped."
