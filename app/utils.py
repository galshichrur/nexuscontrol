import psutil
import socket
import requests
import platform
import datetime
import time
import threading
import state
from getmac import get_mac_address


class SystemStats:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(self.hostname)
        self.public_ip = requests.get('https://api.ipify.org').text
        self.mac_address = get_mac_address()
        self.os_name = platform.system()
        self.os_version = platform.version()
        self.os_architecture = platform.architecture()[0]
        self.server_start_time = str(datetime.datetime.now())

        # Dynamic stats
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.network_download_kbps = 0.0
        self.network_upload_kbps = 0.0
        self.server_time = str(datetime.datetime.now())
        threading.Thread(target=self._background_update, daemon=True).start()

    def _background_update(self):
        while True:
            self.cpu_usage = psutil.cpu_percent(interval=1)
            self.memory_usage = psutil.virtual_memory().percent

            net1 = psutil.net_io_counters()
            time.sleep(5)
            net2 = psutil.net_io_counters()

            recv_rate = (net2.bytes_recv - net1.bytes_recv) / 1024
            sent_rate = (net2.bytes_sent - net1.bytes_sent) / 1024

            self.network_download_kbps = round(recv_rate, 2)
            self.network_upload_kbps = round(sent_rate, 2)
            self.server_time = str(datetime.datetime.now())

system_stats = SystemStats()