import subprocess
import os

def run_command(cmd: str) -> tuple[str, str]:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    cwd = os.getcwd()

    if result.stderr:
        return f"Error: {result.stderr}", cwd
    return result.stdout.strip(), cwd
