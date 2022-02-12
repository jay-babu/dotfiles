#!/usr/bin/env bash

folderNames=(
    "linux" # Must be first
    "fish"
)

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for folder in "${folderNames[@]}"; do
    chmod u+x "$SCRIPT_DIR/$folder/setup.sh"
    "$SCRIPT_DIR/$folder/setup.sh"
done

