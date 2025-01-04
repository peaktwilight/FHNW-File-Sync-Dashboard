import os
import subprocess
import time
import logging
import configparser
import shutil
import sys
import platform

def check_prerequisites():
    """Checks if required tools are installed."""
    if platform.system() == "Windows":
        if not shutil.which('robocopy'):
            logging.error("robocopy is not installed. Please install it and try again.")
            return False
    else:
        if not shutil.which('rsync'):
            logging.error("rsync is not installed. Please install it and try again.")
            return False
            
    if not shutil.which('git'):
        logging.error("git is not installed. Please install it and try again.")
        return False
    return True

def load_config():
    """Loads the configuration from config.txt."""
    config = configparser.ConfigParser()
    if not os.path.exists('config.txt'):
        logging.error("config.txt not found. Please create it and try again.")
        return None
    config.read('config.txt')
    return config

# Configure logging
def setup_logging(log_level):
    """Sets up logging based on the config."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Change logging to write directly to stdout without buffering
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stdout,  # Use stdout instead of stderr
        force=True
    )
    # Ensure stdout is line buffered
    sys.stdout.reconfigure(line_buffering=True)

def retry_rsync(source_path, target_dir, max_retries):
    """Retries sync command with platform-specific tools."""
    for attempt in range(1, max_retries + 1):
        logging.info(f"Attempting to copy from {source_path} to {target_dir} (Try #{attempt})")
        try:
            if platform.system() == "Windows":
                # Use robocopy on Windows
                process = subprocess.Popen(
                    ['robocopy', source_path, target_dir, '/E', '/XO', '/NP', '/MT:8'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            else:
                # Use rsync on macOS/Linux
                process = subprocess.Popen(
                    ['rsync', '-avh', '--progress', '--ignore-existing', '--update', 
                     f"{source_path}/", f"{target_dir}/"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            
            # Real-time output processing
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip(), flush=True)
                    logging.info(output.strip())
            
            stderr = process.stderr.read()
            if stderr:
                print(f"Error: {stderr}", flush=True)
                logging.error(stderr)

            # Check for errors - handle platform-specific return codes
            if platform.system() == "Windows":
                # Robocopy success codes are 0-7
                if process.returncode <= 7:
                    return True
                else:
                    logging.error(f"robocopy failed with exit code {process.returncode}")
                    return False
            else:
                # rsync success code is 0, partial success is 24
                if process.returncode == 0:
                    return True
                elif process.returncode == 24:
                    logging.warning(f"Some files vanished, retrying... (Attempt {attempt}/{max_retries})")
                    time.sleep(1)
                else:
                    logging.error(f"rsync failed with exit code {process.returncode}")
                    return False
                
        except Exception as e:
            logging.error(f"Error during rsync: {str(e)}")
            return False
            
    logging.error(f"Failed to sync after {max_retries} attempts. Some files may have been skipped.")
    return False

def git_pull(repo_path):
    """Performs a git pull if the directory is a git repository."""
    if os.path.isdir(repo_path) and os.path.isdir(os.path.join(repo_path, ".git")):
        logging.info(f"Performing git pull for {repo_path}...")
        try:
            subprocess.run(['git', 'pull'], cwd=repo_path, check=True, capture_output=True)
            logging.info(f"git pull successful for {repo_path}")
        except subprocess.CalledProcessError as e:
            logging.error(f"git pull failed for {repo_path} with exit code {e.returncode}: {e.stderr.decode()}")
    else:
        logging.warning(f"Git repository not found at {repo_path}, skipping git pull.")

def execute_script(script_path):
    """Executes a script if it exists and is executable."""
    if os.path.isfile(script_path) and os.access(script_path, os.X_OK):
        logging.info(f"Executing script: {script_path}")
        try:
             subprocess.run([script_path], check=True, capture_output=True)
             logging.info(f"Script {script_path} executed successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Script {script_path} failed with exit code {e.returncode}: {e.stderr.decode()}")
    else:
        logging.warning(f"Script not found or not executable at {script_path}, skipping.")

def main():
    """Main function to synchronize directories, perform git pull, and execute scripts."""
    if not check_prerequisites():
        return

    config = load_config()
    if not config:
        return

    log_level = config['DEFAULT'].get('log_level', 'INFO')
    setup_logging(log_level)

    destination = config['DEFAULT']['destination']
    source_paths = [path.strip() for path in config['DEFAULT']['source_paths'].split(',')]
    oop_repo_path = config['DEFAULT'].get('oop_repo_path')
    swegl_script_path = config['DEFAULT'].get('swegl_script_path')
    max_rsync_retries = int(config['DEFAULT'].get('max_rsync_retries', 3))
    enable_git_pull = config['DEFAULT'].getboolean('enable_git_pull', True)
    enable_swegl_script = config['DEFAULT'].getboolean('enable_swegl_script', True)

    logging.info(f"Script started, destination: {destination}")

    for source_path in source_paths:
        if not os.path.exists(source_path):
            logging.warning(f"Source path {source_path} does not exist, skipping.")
            continue
        folder_name = os.path.basename(source_path)
        target_dir = os.path.join(destination, folder_name)
        logging.info(f"Creating directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
        if retry_rsync(source_path, target_dir, max_rsync_retries):
            logging.info(f"Successfully synced {source_path} to {target_dir}")
        else:
            logging.error(f"Failed to sync {source_path} to {target_dir}")

    if enable_git_pull and oop_repo_path:
        git_pull(oop_repo_path)
    elif not oop_repo_path:
        logging.warning("oop_repo_path not defined in config.txt, skipping git pull.")
    else:
        logging.info("Git pull disabled in config.txt.")

    if enable_swegl_script and swegl_script_path:
        execute_script(swegl_script_path)
    elif not swegl_script_path:
        logging.warning("swegl_script_path not defined in config.txt, skipping script execution.")
    else:
        logging.info("SWEGL script execution disabled in config.txt.")

    logging.info("All tasks completed!")

if __name__ == "__main__":
    main()
