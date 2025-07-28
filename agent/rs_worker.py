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
SLEEP_INTERVAL: float = 120


def get_uuid(s: socket.socket) -> str:

    if os.path.exists(AGENT_ID_FILENAME):
        with open(AGENT_ID_FILENAME, "r") as f:
            return f.read().strip()
    else:
        uid = first_time_connect(s)
        with open(AGENT_ID_FILENAME, "w") as f:
            f.write(uid)
        return uid

def first_time_connect(s: socket.socket) -> str:

    # Send connection details to server
    s.send(json.dumps(connection_details).encode().strip())

    # Receive assigned agent_id
    return s.recv(BUFFER_SIZE).decode().strip()

def ping(agent_id: str, s: socket.socket) -> None:

    while True:
        time.sleep(SLEEP_INTERVAL)

        # Add agent_id to connection details.
        data = connection_details
        data["agent_id"] = agent_id

        s.send(json.dumps(data).encode().strip())

def main() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_HOST, SERVER_PORT))
    agent_id = get_uuid(s)
    ping(agent_id, s)

if __name__ == '__main__':
    main()