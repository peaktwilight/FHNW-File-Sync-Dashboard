# FHNW Sync Script

This script synchronizes files from various source directories on a mounted volume to a local destination directory. It also performs a `git pull` for the `oopI2` repository and triggers a script for the `sweGL` repository.

## Prerequisites

-   The script assumes that the source directories are located on a mounted volume at `/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/`.
-   The destination directory is set to `/Users/peak/Documents/Study/FHNW`.
-   The `oopI2` repository is expected to be located at `/Users/peak/Documents/Study/FHNW/oopI2/oopI2-aufgaben_doruk.oeztuerk`.
-   The `fetch_from_origin.sh` script for `sweGL` is expected to be located at `/Users/peak/Documents/Study/FHNW/sweGL/fhnw-swegl-aufgaben-24-hs/fetch_from_origin.sh`.
-   `rsync` must be installed on your system.
-   `git` must be installed on your system.

## How to Use

1.  Save the `sync_fhnw.sh` script to a file.
2.  Make the script executable: `chmod +x sync_fhnw.sh`.
3.  Run the script: `./sync_fhnw.sh`.

## Script Details

The script performs the following actions:

1.  **Synchronizes directories:** It copies the following directories from the mounted volume to the destination directory:
    -   `sweGL`
    -   `oopI2`
    -   `pmC`
    -   `mgli`
    Each directory is copied into its own subdirectory within the destination directory.
2.  **Performs git pull for `oopI2`:** If the `oopI2` repository is found, it performs a `git pull` to update the local repository.
3.  **Triggers `fetch_from_origin.sh` for `sweGL`:** If the `fetch_from_origin.sh` script is found and executable, it runs the script.

## Configuration

-   **`DESTINATION`**: The destination directory where the files will be copied.
-   **`SOURCE_PATHS`**: An array of source directories to be copied.

You can modify these variables directly in the script if needed.

## Error Handling

-   The script uses `set -euo pipefail` to exit immediately if any command fails.
-   The script retries `rsync` up to 3 times if some files vanish during the copy process.
-   The script checks if the directories exist before performing `git pull` and if the `fetch_from_origin.sh` script exists and is executable before running it.
-   The script logs errors to the console.

## Logging

The script outputs timestamps and messages to the console to indicate what it is doing.
