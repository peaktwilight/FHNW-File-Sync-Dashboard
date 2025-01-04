#!/bin/bash

# Use strict mode
set -euo pipefail

# Get current timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "Script started at: $TIMESTAMP"


# Retry function for rsync
retry_rsync() {
    local SOURCE_PATH=$1
    local TARGET_DIR=$2
    local MAX_RETRIES=3
    local RETRY_COUNT=0
    local SUCCESS=false

    until [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; do
        echo "Attempting to copy from $SOURCE_PATH to $TARGET_DIR (Try #$((RETRY_COUNT + 1)))"
        rsync -avh --progress --ignore-existing --update "$SOURCE_PATH/" "$TARGET_DIR/"
        if [ $? -eq 24 ]; then
            echo "Some files vanished, retrying..."
            RETRY_COUNT=$((RETRY_COUNT + 1))
        else
            SUCCESS=true
            break
        fi

    done

    if [ "$SUCCESS" = false ]; then
        echo "Failed to sync after $MAX_RETRIES attempts. Some files may have been skipped."
    fi
}
# Configuration
DESTINATION="/Users/peak/Documents/Study/FHNW"
SOURCE_PATHS=(
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1iCbb/sweGL"
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1Ia/oopI2"
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1iCa/pmC"
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1iCbb/mgli"
)


# Loop through each source path and copy to destination into its own subdirectory
for SOURCE_PATH in "${SOURCE_PATHS[@]}"; do
    FOLDER_NAME=$(basename "$SOURCE_PATH")
    TARGET_DIR="$DESTINATION/$FOLDER_NAME"
    echo "Creating directory: $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
    if [ $? -ne 0 ]; then
        echo "Error creating directory: $TARGET_DIR"
        exit 1
    fi
    retry_rsync "$SOURCE_PATH" "$TARGET_DIR"
done


# Perform git pull for oopI2 repo
OOP_REPO_PATH="$DESTINATION/oopI2/oopI2-aufgaben_doruk.oeztuerk"
if [ -d "$OOP_REPO_PATH" ] && [ -d "$OOP_REPO_PATH/.git" ]; then
    echo "Performing git pull for OOPL2..."
    cd "$OOP_REPO_PATH"
    git pull
else
    echo "OOPL2 git repository not found at $OOP_REPO_PATH, skipping git pull."
fi

echo "Syncing completed!"
echo "------------------"
echo "------------------"




echo "------------------"
echo "------------------"


# Trigger the fetch_from_origin.sh script for SWEGL
SWEGL_SCRIPT_PATH="$DESTINATION/sweGL/fhnw-swegl-aufgaben-24-hs/fetch_from_origin.sh"
if [ -x "$SWEGL_SCRIPT_PATH" ]; then
    echo "Triggering fetch_from_origin.sh for SWEGL..."
    "$SWEGL_SCRIPT_PATH"
else
    echo "fetch_from_origin.sh not found or not executable at $SWEGL_SCRIPT_PATH, skipping."
fi


echo "All tasks completed!"
