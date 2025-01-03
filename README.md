# FHNW Course Material Repository

This repository contains course materials from my studies at the FHNW (University of Applied Sciences and Arts Northwestern Switzerland). It includes assignments, notes, and other resources for various modules.

## Repository Structure

The repository is organized into the following main directories:

-   `dtpC`: Contains materials for the "Desktop Publishing and Communication" module.
-   `mgli`: Contains materials for the "Mathematics and Grundlagen der Informatik" module.
-   `oopI2`: Contains materials for the "Object-Oriented Programming I2" module.
-   `pmC`: Contains materials for the "Project Management and Communication" module.

Each of these directories may contain subdirectories for specific exercises, projects, or topics.

## Synchronization Script

The `sync_fhnw.py` script is used to synchronize the course materials from a mounted volume to a local directory. It also performs a `git pull` for the `oopI2` repository and triggers a script for the `sweGL` repository.

### Prerequisites

-   Python 3.6 or higher
-   The source directories are located on a mounted volume at `/Volumes/data/HT/E1811_Unterrichte_Bachelor/E1811_Unterrichte_I/`.
-   The destination directory is set in the `config.txt` file (default: `/Users/peak/Documents/Study/FHNW`).
-   The `oopI2` repository is expected to be located at the path specified in `config.txt` (default: `/Users/peak/Documents/Study/FHNW/oopI2/oopI2-aufgaben_doruk.oeztuerk`).
-   The `fetch_from_origin.sh` script for `sweGL` is expected to be located at the path specified in `config.txt` (default: `/Users/peak/Documents/Study/FHNW/sweGL/fhnw-swegl-aufgaben-24-hs/fetch_from_origin.sh`).
-   `rsync` must be installed on your system.
-   `git` must be installed on your system.

### How to Use

1.  Save the `sync_fhnw.py` script and `config.txt` to the root of the repository.
2.  Install the required Python packages: `pip install configparser`
3.  Run the script: `python sync_fhnw.py`.

### Configuration

The `config.txt` file contains the following configuration options:

-   **`destination`**: The destination directory where the files will be copied.
-   **`source_paths`**: A comma-separated list of source directories to be copied.
-   **`oop_repo_path`**: The path to the `oopI2` git repository.
-   **`swegl_script_path`**: The path to the `fetch_from_origin.sh` script for `sweGL`.

You can modify these variables in the `config.txt` file.

### Error Handling

-   The script uses `try-except` blocks to catch errors.
-   The script retries `rsync` up to 3 times if some files vanish during the copy process.
-   The script checks if the directories exist before performing `git pull` and if the `fetch_from_origin.sh` script exists and is executable before running it.
-   The script logs errors to the console.

### Logging

The script outputs timestamps and messages to the console to indicate what it is doing.
