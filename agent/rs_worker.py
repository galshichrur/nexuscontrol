import os
import sys
import socket
import json
import time
from data import connection_details

SERVER_HOST: str = sys.argv[1]
SERVER_PORT: int = int(sys.argv[2])
BUFFER_SIZE: int = 1024
SEPARATOR: str = "<sep>"
AGENT_ID_FILENAME = "uuid.txt"
SLEEP_INTERVAL: float = 90
RECV_TIMEOUT = 2

def get_uuid() -> str | None:

    if os.path.exists(AGENT_ID_FILENAME):
        with open(AGENT_ID_FILENAME, "r") as f:
            data = f.read()[1:-1]
            print(data)
            if data:
                return data
            else:
                return None

    return None

def connect(s: socket.socket) -> None:
    agent_id = get_uuid()

    if agent_id is not None:
        connection_details["agent_id"] = agent_id

    data = json.dumps(connection_details)
    s.send(data.encode())

    agent_uid = s.recv(BUFFER_SIZE).decode().strip()
    with open(AGENT_ID_FILENAME, "w") as f:
        f.write(agent_uid)
    print(agent_uid)
    while True:
        s.send(json.dumps(agent_uid).encode())
        print("Sent ping")
        try:
            command = s.recv(BUFFER_SIZE)
            if command:
                pass
        except socket.timeout:
            pass
        time.sleep(SLEEP_INTERVAL)

def main() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_HOST, SERVER_PORT))
    s.settimeout(RECV_TIMEOUT)
    connect(s)

if __name__ == '__main__':
    main()