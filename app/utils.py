import psutil
import socket
import requests
import platform
import datetime
import time
from typing import Generator
from getmac import get_mac_address


hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
public_ip = requests.get('https://api.ipify.org').text
mac_address = get_mac_address()
cpu_usage = psutil.cpu_percent(10)
memory_usage = psutil.virtual_memory().percent
os_name = platform.system()
os_version = platform.version()
os_architecture = platform.architecture()[0]
server_time = str(datetime.datetime.now())


def get_network_usage(interval: int = 10) -> Generator[tuple[float, float], None, None]:
    last_bytes_sent = psutil.net_io_counters().bytes_sent
    last_bytes_recv = psutil.net_io_counters().bytes_recv

    while True:
        time.sleep(interval)
        current_bytes_sent = psutil.net_io_counters().bytes_sent
        current_bytes_recv = psutil.net_io_counters().bytes_recv

        bytes_sent_diff = current_bytes_sent - last_bytes_sent
        bytes_recv_diff = current_bytes_recv - last_bytes_recv

        yield (bytes_recv_diff / interval), (bytes_sent_diff / interval)

        last_bytes_sent = current_bytes_sent
        last_bytes_recv = current_bytes_recv


network_usage = get_network_usage()
while True:
    network_download_kbps, network_upload_kbps = next(network_usage)
