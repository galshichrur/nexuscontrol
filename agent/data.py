import platform
import requests
import socket
import os
from getmac import get_mac_address
import ctypes
import getpass


def is_admin():
    try:
        # For Unix-like systems
        is_admin_status = (os.getuid() == 0)
    except AttributeError:
        # For Windows systems
        is_admin_status = (ctypes.windll.shell32.IsUserAnAdmin() != 0)
    return is_admin_status

def get_system_info() -> dict:

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    data: dict = {
        "hostname": hostname,
        "cwd": os.getcwd(),
        "os_name": platform.system(),
        "os_version": platform.version(),
        "os_architecture": platform.architecture()[0],
        "local_ip": local_ip,
        "public_ip": requests.get('https://api.ipify.org').text,
        "mac_address": get_mac_address(),
        "is_admin": is_admin(),
        "username": getpass.getuser()
    }

    return data