#!/bin/bash

# Check if a path is provided
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path>"
  exit 1
fi

# The path to the directory
DIR_PATH="$1"

# Iterate over each folder in the specified path
for folder in "$DIR_PATH"/*/; do
  # Check if it's a directory
  if [ -d "$folder" ]; then
    # Get the folder name
    folder_name=$(basename "$folder")
    # Create a compressed tar file using zstd
    tar --use-compress-program=zstd -cf "$DIR_PATH/$folder_name.tar.zst" -C "$DIR_PATH" "$folder_name"
    echo "Compressed $folder_name to $folder_name.tar.zst"
  fi
done