import os
import subprocess
import time
import logging
import configparser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def retry_rsync(source_path, target_dir, max_retries=3):
    """Retries rsync command if it fails with exit code 24."""
    for attempt in range(1, max_retries + 1):
        logging.info(f"Attempting to copy from {source_path} to {target_dir} (Try #{attempt})")
        try:
            result = subprocess.run(
                ['rsync', '-avh', '--progress', '--ignore-existing', '--update', f"{source_path}/", f"{target_dir}/"],
                check=True,
                capture_output=True
            )
            logging.info(f"rsync output: {result.stdout.decode()}")
            return True
        except subprocess.CalledProcessError as e:
            if e.returncode == 24:
                logging.warning(f"Some files vanished, retrying... (Attempt {attempt}/{max_retries})")
                time.sleep(1)  # Wait a bit before retrying
            else:
                logging.error(f"rsync failed with exit code {e.returncode}: {e.stderr.decode()}")
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
    config = configparser.ConfigParser()
    config.read('config.txt')

    destination = config['DEFAULT']['destination']
    source_paths = [path.strip() for path in config['DEFAULT']['source_paths'].split(',')]
    oop_repo_path = config['DEFAULT']['oop_repo_path']
    swegl_script_path = config['DEFAULT']['swegl_script_path']

    logging.info(f"Script started, destination: {destination}")

    for source_path in source_paths:
        folder_name = os.path.basename(source_path)
        target_dir = os.path.join(destination, folder_name)
        logging.info(f"Creating directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
        if retry_rsync(source_path, target_dir):
            logging.info(f"Successfully synced {source_path} to {target_dir}")
        else:
            logging.error(f"Failed to sync {source_path} to {target_dir}")

    git_pull(oop_repo_path)
    execute_script(swegl_script_path)

    logging.info("All tasks completed!")

if __name__ == "__main__":
    main()
