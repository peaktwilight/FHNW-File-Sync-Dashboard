#!/bin/bash

# Retry function for rsync
retry_rsync() {
    local SRC=$1
    local TARGET_DIR=$2
    local MAX_RETRIES=3
    local RETRY_COUNT=0
    local SUCCESS=false

    until [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; do
        echo "Attempting to copy from $SRC to $TARGET_DIR (Try #$((RETRY_COUNT + 1)))"
        rsync -avh --progress --ignore-existing --update "$SRC/" "$TARGET_DIR/"
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

# Source paths
SOURCE_PATHS=(
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1iCbb/sweGL"
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1Ia/oopI2"
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1iCa/pmC"
    "/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/1iCbb/mgli"
)

# Destination path
DESTINATION="/Users/peak/Documents/Study/FHNW"

# Loop through each source path and copy to destination into its own subdirectory
for SRC in "${SOURCE_PATHS[@]}"; do
    FOLDER_NAME=$(basename "$SRC")
    TARGET_DIR="$DESTINATION/$FOLDER_NAME"
    mkdir -p "$TARGET_DIR"
    retry_rsync "$SRC" "$TARGET_DIR"
done

echo "Syncing completed!"
echo "------------------"
echo "------------------"

# Perform git pull for oopI2 repo
echo "Performing git pull for OOPL2..."
cd /Users/peak/Documents/Study/FHNW/OOPL2/oopI2-aufgaben_doruk.oeztuerk
git pull

echo "------------------"
echo "------------------"

# Trigger the fetch_from_origin.sh script for SWEGL
echo "Triggering fetch_from_origin.sh for SWEGL..."
/Users/peak/Documents/Study/FHNW/SWEGL/fhnw-swegl-aufgaben-24-hs/fetch_from_origin.sh

echo "All tasks completed!"
