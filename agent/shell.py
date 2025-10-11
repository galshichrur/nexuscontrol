import subprocess
import os

def run_command(cmd: str) -> tuple[str, str]:
    # Handle "cd" command
    if cmd.startswith("cd"):
        parts = cmd.split(maxsplit=1)
        if len(parts) == 1:
            new_dir = os.path.expanduser("~")
        else:
            new_dir = os.path.expanduser(parts[1])
            new_dir = os.path.abspath(os.path.join(os.getcwd(), new_dir))
        try:
            os.chdir(new_dir)
            return "", os.getcwd()
        except Exception as e:
            return str(e), os.getcwd()

    # Handle all other commands
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    cwd = os.getcwd()

    if result.stderr:
        return f"Error: {result.stderr}", cwd
    return result.stdout, cwd
