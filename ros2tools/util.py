import subprocess
import json
import os
import shutil
import sys

def check_command_installed(command):
    """Checks if the given command is installed."""
    if shutil.which(command) is None:
        raise Exception(f"ERROR: The command '{command}' is not installed or not found in the system PATH. Install the command and try again.")

def mkdirp(path):
    """
    Creates a directory and all necessary parent directories.
    Similar to the `mkdir -p` command in Unix-like systems.

    Parameters:
        path (str): The directory path to create.

    Returns:
        None
    """
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Directory created: {path}")
    except Exception as e:
        print(f"Error creating directory {path}: {e}")

def run_command(command, timeout=5, echo=False, echo_out=False):
    """
    Run a shell command with a specified timeout and return both stdout and stderr.
    In case of errors, return a tuple of empty strings for both stdout and stderr.
    
    Parameters:
        command (str): The shell command to run.
        timeout (int): The timeout for the command execution in seconds. Default is 5.
        echo (bool): If True, print the shell command being executed. Default is False.
        echo_out (bool): If True, print the stdout and stderr output with prefixes. Default is True.
    
    Returns:
        tuple: stdout and stderr as strings.
    """
    if echo:
        print(f"executing shell command: {command}", file=sys.stderr)

    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        
        stdout_output = result.stdout.strip()
        stderr_output = result.stderr.strip()

        if echo_out:
            if stdout_output:
                print(f"  stdout:\n    {stdout_output}")
            if stderr_output:
                print(f"  stderr:\n    {stderr_output}")

        return stdout_output, stderr_output

    except subprocess.TimeoutExpired:
        print("Timeout expired while executing the command.")
        return "", f"Command timed out after {timeout} seconds"
    except subprocess.CalledProcessError as e:
        stdout_output = e.stdout.strip() if e.stdout else ""
        stderr_output = e.stderr.strip() if e.stderr else ""
        if echo_out:
            print(f"  stdout:\n {stdout_output}")
            print(f"  stderr:\n {stderr_output}")
        return stdout_output, stderr_output
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return "", str(e)



def write_json_file(output_path, data):
    try:
        if not data:
            raise IOError(f"ERROR: The provided data is null, nothing to write to: {output_path} skipping.")
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"JSON file written to {output_path}")
    except IOError as e:
        print(f"Error writing to file: {e}")
        sys.exit(1)

