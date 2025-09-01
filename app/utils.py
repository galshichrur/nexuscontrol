import psutil
import socket
import requests
import platform
import datetime
import time
from getmac import get_mac_address


def get_network_usage(interval: int = 1) -> tuple[float, float]:
    last_bytes_sent = psutil.net_io_counters().bytes_sent
    last_bytes_recv = psutil.net_io_counters().bytes_recv

    time.sleep(interval)
    current_bytes_sent = psutil.net_io_counters().bytes_sent
    current_bytes_recv = psutil.net_io_counters().bytes_recv

    bytes_sent_diff = current_bytes_sent - last_bytes_sent
    bytes_recv_diff = current_bytes_recv - last_bytes_recv

    return round((bytes_recv_diff / interval), 2), round((bytes_sent_diff / interval), 2)

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
public_ip = requests.get('https://api.ipify.org').text
mac_address = get_mac_address()
cpu_usage = psutil.cpu_percent(1)
memory_usage = psutil.virtual_memory().percent
os_name = platform.system()
os_version = platform.version()
os_architecture = platform.architecture()[0]
server_time = str(datetime.datetime.now())
network_download_kbps, network_upload_kbps = get_network_usage()
server_start_time = str(datetime.datetime.now())

def update():
    global cpu_usage, memory_usage, server_time, network_upload_kbps, network_download_kbps
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    server_time = str(datetime.datetime.now())
    network_download_kbps, network_upload_kbps = get_network_usage()
