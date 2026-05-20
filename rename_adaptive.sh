#!/bin/bash

# Script to rename files by replacing "_adaptive_" with "_"
# Usage: ./rename_adaptive.sh [directory]

# Set target directory (current directory if none provided)
TARGET_DIR="${1:-.}"

# Check if directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist."
    exit 1
fi

# Change to target directory
cd "$TARGET_DIR" || exit 1

# Counter for renamed files
renamed_count=0

# Process files containing "_adaptive_"
for file in *_adaptive_*; do
    # Check if the pattern actually matches any files
    if [ ! -e "$file" ]; then
        echo "No files containing '_adaptive_' found in $(pwd)"
        break
    fi
    
    # Generate new filename by replacing "_adaptive_" with "_"
    newfile="${file//_adaptive_/_}"
    
    # Check if new filename already exists
    if [ -e "$newfile" ]; then
        echo "Warning: Cannot rename '$file' - '$newfile' already exists. Skipping."
        continue
    fi
    
    # Rename the file
    echo "Renaming: '$file' -> '$newfile'"
    mv "$file" "$newfile"
    ((renamed_count++))
done

# Summary
echo "Done. Renamed $renamed_count file(s)."
