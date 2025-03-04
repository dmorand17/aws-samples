#!/bin/bash

set -euo pipefail

# Create a set of files from 1MB to 1GB
MAX_FILE_SIZE=500
FILE_SIZE_INCREMENT=50
OUTPUT_DIR="tmp"

# Check if the output directory exists
if [[ ! -d "$OUTPUT_DIR" ]]; then
  mkdir "$OUTPUT_DIR"
else
  echo "[-] Output directory already exists. Re-creating..."
  rm -rf "$OUTPUT_DIR"
  mkdir "$OUTPUT_DIR"
fi

echo "[+] Created output directory: $OUTPUT_DIR"

# Function to create a file of specified size
create_file() {
    local size=$1
    local filename="file_${size}MB.dat"
    dd if=/dev/urandom of="$OUTPUT_DIR/$filename" bs=1M count="$size" &> /dev/null
    echo "[+] Created $filename"
}

# Create files from 1MB to 1GB in 100MB increments
for size in $(seq 1 $FILE_SIZE_INCREMENT $MAX_FILE_SIZE); do
    create_file "$size"
done

echo "[+] Finished!"
